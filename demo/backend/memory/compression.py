"""
Step 2 — Context Pruning and Compression

Demonstrates:
  • Rolling conversation summaries
  • Token counting + budget enforcement
  • Hierarchical summarization (messages → summary)
"""

import json
import logging

from google import genai

log = logging.getLogger(__name__)


SUMMARIZE_PROMPT = """You are a memory compression engine. Summarize the following conversation
into a concise paragraph that preserves:
1. Key decisions made
2. User preferences or constraints mentioned
3. Important facts or outcomes
4. Any unresolved questions or next steps

Be factual and concise. Do NOT add opinions.

Conversation:
{conversation}

Existing summary to update (if any):
{existing_summary}

Updated summary:"""

EXTRACT_MEMORIES_PROMPT = """Analyze this conversation turn and extract any information worth
remembering long-term. Return a JSON array of objects, each with:
- "text": the memory content
- "type": one of "preference", "fact", "decision", "constraint", "correction"

If nothing is worth remembering, return an empty array [].

Only extract EXPLICIT information stated by the user. Do NOT infer or assume.

User message: {user_message}
Assistant response: {assistant_response}

JSON array:"""

EXTRACT_PROFILE_PROMPT = """Analyze this conversation and extract any user profile updates.
Return a JSON object with these optional keys:
- "name": user's name if mentioned
- "preferences": dict of preference key-value pairs
- "constraints": list of constraint strings
- "facts": list of factual statements about the user

Only include keys where you found explicit information. Return {{}} if nothing found.

User message: {user_message}
Assistant response: {assistant_response}

JSON object:"""


class CompressionEngine:
    """Handles rolling summarization and memory extraction."""

    SUMMARY_TRIGGER_MESSAGES = 6  # summarize every N messages
    MAX_CONTEXT_TOKENS = 2000     # token budget for conversation history

    def __init__(self, gemini_client: genai.Client, model: str = "gemini-3-flash-preview"):
        self.client = gemini_client
        self.model = model

    def count_tokens(self, text: str) -> int:
        """Approximate token count (≈4 chars per token for English)."""
        return len(text) // 4

    def should_summarize(self, messages: list[dict]) -> bool:
        """Check if we've accumulated enough messages to trigger summarization."""
        return len(messages) >= self.SUMMARY_TRIGGER_MESSAGES

    def _generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 300) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text.strip()

    def _generate_json(self, prompt: str, temperature: float = 0.0, max_tokens: int = 1024) -> str:
        """Generate with Gemini JSON mode — guarantees valid JSON output."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            ),
        )
        return response.text.strip()

    def rolling_summarize(self, messages: list[dict], existing_summary: str | None = None) -> str:
        """Produce a rolling summary of the conversation so far."""
        conversation = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in messages
        )
        prompt = SUMMARIZE_PROMPT.format(
            conversation=conversation,
            existing_summary=existing_summary or "(none)",
        )
        return self._generate(prompt, temperature=0.2, max_tokens=300)

    def extract_memories(self, user_message: str, assistant_response: str) -> list[dict]:
        """Extract memorable facts from a conversation turn."""
        prompt = EXTRACT_MEMORIES_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )
        raw = self._generate_json(prompt)
        log.info(f"extract_memories raw: {raw!r}")
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError) as e:
            log.error(f"extract_memories JSON parse failed: {e}, raw={raw!r}")
            return []

    def extract_profile_updates(self, user_message: str, assistant_response: str) -> dict:
        """Extract user profile updates from a conversation turn."""
        prompt = EXTRACT_PROFILE_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )
        raw = self._generate_json(prompt)
        log.info(f"extract_profile raw: {raw!r}")
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, IndexError) as e:
            log.error(f"extract_profile JSON parse failed: {e}, raw={raw!r}")
            return {}

    def prune_messages_to_budget(
        self,
        messages: list[dict],
        summary: str | None,
        token_budget: int | None = None,
    ) -> tuple[list[dict], dict]:
        """
        Prune conversation history to fit within a token budget.
        Returns (pruned_messages, stats).
        """
        budget = token_budget or self.MAX_CONTEXT_TOKENS
        total_tokens = sum(self.count_tokens(m["content"]) for m in messages)

        stats = {
            "original_messages": len(messages),
            "original_tokens": total_tokens,
            "budget": budget,
            "pruned": False,
            "strategy": "none",
        }

        if total_tokens <= budget:
            stats["final_messages"] = len(messages)
            stats["final_tokens"] = total_tokens
            return messages, stats

        # Strategy: keep summary + most recent messages that fit
        kept = []
        used = 0
        for m in reversed(messages):
            t = self.count_tokens(m["content"])
            if used + t > budget:
                break
            kept.insert(0, m)
            used += t

        stats.update({
            "pruned": True,
            "strategy": "keep_recent_with_summary",
            "final_messages": len(kept),
            "final_tokens": used,
            "dropped_messages": len(messages) - len(kept),
        })
        return kept, stats
