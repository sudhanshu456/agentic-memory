"""
OpsAgent — AI SRE Assistant with Full Memory Stack

Orchestrates the complete agent loop:
  Read → Retrieve → Assemble → Act → Evaluate → Write-back

Each step maps to a blog section:
  Step 1: Vector store retrieval (Milvus Lite)
  Step 2: Context pruning & compression (rolling summaries)
  Step 3: Cross-session persistence (user profile + episodic memory)
  Bonus:  Progressive disclosure (skills-based loading)
"""

import logging
import uuid

from google import genai

from memory.vector_store import VectorMemoryStore
from memory.user_profile import UserProfileStore
from memory.session_store import SessionStore
from memory.compression import CompressionEngine
from memory.skills import SkillsLoader

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are **OpsAgent**, an AI SRE / Platform Engineering assistant.

Your responsibilities:
- Help engineers triage incidents, diagnose outages, and perform root-cause analysis.
- Guide deployments, rollbacks, and release management.
- Advise on capacity planning, autoscaling, and resource optimisation.
- Assist with monitoring, alerting, SLOs, and observability setup.
- Remember user preferences, infrastructure context, and past incidents across sessions.

Behavior rules:
- Be concise and actionable. SREs are busy — get to the point.
- When suggesting commands, always include the namespace placeholder.
- If you recall relevant past incidents or user preferences from memory, reference them naturally.
- If a runbook/skill was loaded for this query, follow its structure.
- When you learn new facts about the user's stack or preferences, acknowledge them briefly.

{context_blocks}
"""


class OpsAgent:
    """Full-stack agent with memory: retrieve → assemble → act → write-back."""

    def __init__(self, gemini_client: genai.Client, model: str = "gemini-3-flash-preview"):
        self.gemini = gemini_client
        self.model = model

        # Gemini embedding function (gemini-embedding-001, 768 dims)
        def embed_fn(text: str) -> list[float]:
            result = gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
            )
            return result.embeddings[0].values

        # Memory subsystems
        self.vector_store = VectorMemoryStore(embed_fn=embed_fn)
        self.profile_store = UserProfileStore()
        self.session_store = SessionStore()
        self.compression = CompressionEngine(gemini_client, model)
        self.skills = SkillsLoader()

    async def chat(self, user_id: str, session_id: str, message: str) -> dict:
        """
        Full agent loop. Returns the response + detailed debug/inspector metadata
        so the frontend can visualise every memory operation.
        """
        debug = {
            "steps": [],
            "retrieved_memories": [],
            "profile": {},
            "episodic_context": None,
            "skills_loaded": [],
            "compression_stats": None,
            "new_memories": [],
            "profile_updates": {},
            "summary": None,
        }

        # ── 1. Read: store user message ────────────────────────────────
        self.session_store.add_message(user_id, session_id, "user", message)
        debug["steps"].append("stored_user_message")

        # ── 2. Retrieve: semantic memories from vector DB ──────────────
        retrieved = self.vector_store.retrieve_memories(message, user_id, top_k=5)
        memory_context = VectorMemoryStore.format_context_block(retrieved)
        debug["retrieved_memories"] = retrieved
        debug["steps"].append(f"retrieved_{len(retrieved)}_memories")

        # ── 3. Retrieve: user profile (cross-session persistence) ──────
        profile = self.profile_store.get_profile(user_id)
        profile_context = self.profile_store.format_profile_context(user_id)
        debug["profile"] = profile
        debug["steps"].append("loaded_user_profile")

        # ── 4. Retrieve: episodic context from previous session ────────
        episodic_context = self.session_store.format_episodic_context(user_id, session_id)
        debug["episodic_context"] = episodic_context or None
        if episodic_context:
            debug["steps"].append("loaded_episodic_context")

        # ── 5. Progressive disclosure: match & expand skills ───────────
        skills_context, skills_metadata = self.skills.get_expanded_context(message)
        debug["skills_loaded"] = skills_metadata
        loaded_names = [s["name"] for s in skills_metadata if s.get("loaded")]
        if loaded_names:
            debug["steps"].append(f"expanded_skills: {', '.join(loaded_names)}")
        else:
            debug["steps"].append("no_skills_matched")

        # ── 6. Assemble: build context-budgeted prompt ─────────────────
        session = self.session_store.get_session(user_id, session_id)
        messages = session.get("messages", []) if session else []

        # Prune conversation history to token budget
        pruned_messages, compression_stats = self.compression.prune_messages_to_budget(
            messages, session.get("summary") if session else None
        )
        debug["compression_stats"] = compression_stats
        if compression_stats.get("pruned"):
            debug["steps"].append(f"pruned_history: {compression_stats['dropped_messages']} msgs dropped")

        # Build context blocks
        context_parts = []
        if profile_context:
            context_parts.append(profile_context)
        if episodic_context:
            context_parts.append(episodic_context)
        if memory_context:
            context_parts.append(memory_context)
        if skills_context:
            context_parts.append(skills_context)

        # Add rolling summary if available
        if session and session.get("summary"):
            context_parts.append(
                f"<conversation_summary>\n  {session['summary']}\n</conversation_summary>"
            )

        system_prompt = SYSTEM_PROMPT.format(
            context_blocks="\n\n".join(context_parts) if context_parts else "(no prior context)"
        )

        # Build Gemini conversation
        gemini_messages = [{"role": "user", "parts": [{"text": system_prompt + "\n\nNow respond to the user's latest message."}]}]
        gemini_messages.append({"role": "model", "parts": [{"text": "Understood. I'm OpsAgent, ready to help. I've loaded the relevant context."}]})

        # Add pruned conversation history
        for m in pruned_messages[:-1]:  # exclude the latest user msg, we'll add it last
            role = "user" if m["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [{"text": m["content"]}]})

        # Latest user message
        gemini_messages.append({"role": "user", "parts": [{"text": message}]})

        debug["steps"].append("assembled_prompt")

        # ── 7. Act: call Gemini ────────────────────────────────────────
        response = self.gemini.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1500,
            ),
        )
        assistant_response = response.text.strip()
        debug["steps"].append("llm_response_generated")

        # ── 8. Write-back: store assistant message ─────────────────────
        self.session_store.add_message(user_id, session_id, "assistant", assistant_response)

        # ── 9. Write-back: extract & upsert new memories ──────────────
        try:
            new_memories = self.compression.extract_memories(message, assistant_response)
            log.info(f"Extracted memories: {new_memories}")
            stored_memories = []
            for mem in new_memories:
                stored = self.vector_store.upsert_memory(
                    text=mem["text"],
                    user_id=user_id,
                    session_id=session_id,
                    memory_type=mem.get("type", "semantic"),
                )
                stored_memories.append(stored)
            debug["new_memories"] = stored_memories
            if stored_memories:
                debug["steps"].append(f"stored_{len(stored_memories)}_new_memories")
        except Exception as e:
            log.error(f"Memory extraction/storage failed: {e}", exc_info=True)

        # ── 10. Write-back: extract & update user profile ──────────────
        try:
            profile_updates = self.compression.extract_profile_updates(message, assistant_response)
            log.info(f"Profile updates: {profile_updates}")
            if profile_updates:
                self.profile_store.update_profile(user_id, profile_updates)
                debug["profile_updates"] = profile_updates
                debug["steps"].append("updated_user_profile")
        except Exception as e:
            log.error(f"Profile update failed: {e}", exc_info=True)

        # ── 11. Compress: rolling summarization if needed ──────────────
        updated_session = self.session_store.get_session(user_id, session_id)
        all_messages = updated_session.get("messages", []) if updated_session else []
        if self.compression.should_summarize(all_messages):
            summary = self.compression.rolling_summarize(
                all_messages, updated_session.get("summary")
            )
            self.session_store.set_summary(user_id, session_id, summary)
            debug["summary"] = summary
            debug["steps"].append("rolling_summary_generated")

        return {
            "response": assistant_response,
            "debug": debug,
        }

    def get_memory_stats(self, user_id: str) -> dict:
        """Return aggregate stats for the memory inspector panel."""
        return {
            "total_memories": self.vector_store.count(user_id),
            "all_memories": self.vector_store.get_all_memories(user_id),
            "profile": self.profile_store.get_profile(user_id),
            "sessions": self.session_store.list_sessions(user_id),
            "skills_index": [
                {"id": s.id, "name": s.name, "summary": s.summary}
                for s in self.skills.index
            ],
        }
