"""
Bonus — Progressive Disclosure (Skills-based Loading)

Inspired by Claude's SKILLS.md pattern:
  1. Agent has a lightweight index of skill *summaries*
  2. On each query, only relevant skills are fully loaded
  3. Saves context window by not loading everything upfront

This is the "just-in-time context retrieval" concept applied to
agent capabilities.
"""

import os
from dataclasses import dataclass


@dataclass
class SkillSummary:
    id: str
    name: str
    summary: str          # short one-liner shown in the index
    file_path: str        # path to full skill content
    keywords: list[str]


class SkillsLoader:
    """Progressive disclosure loader: index ➜ match ➜ expand."""

    def __init__(self, skills_dir: str = "./skills_registry"):
        self.skills_dir = skills_dir
        self.index: list[SkillSummary] = []
        self._load_index()

    def _load_index(self):
        """Parse SKILLS.md to build the lightweight index."""
        index_path = os.path.join(self.skills_dir, "SKILLS.md")
        if not os.path.exists(index_path):
            return

        with open(index_path, "r") as f:
            content = f.read()

        current_skill = None
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("## "):
                # New skill header: ## skill_id — Skill Name
                parts = line[3:].split(" — ", 1)
                if len(parts) == 2:
                    skill_id = parts[0].strip()
                    skill_name = parts[1].strip()
                    current_skill = {
                        "id": skill_id,
                        "name": skill_name,
                        "summary": "",
                        "keywords": [],
                    }
            elif line.startswith("Summary:") and current_skill:
                current_skill["summary"] = line[len("Summary:"):].strip()
            elif line.startswith("Keywords:") and current_skill:
                kw = line[len("Keywords:"):].strip()
                current_skill["keywords"] = [k.strip() for k in kw.split(",")]
                # Skill entry complete
                file_path = os.path.join(self.skills_dir, f"{current_skill['id']}.md")
                self.index.append(SkillSummary(
                    id=current_skill["id"],
                    name=current_skill["name"],
                    summary=current_skill["summary"],
                    file_path=file_path,
                    keywords=current_skill["keywords"],
                ))
                current_skill = None

    def get_index_context(self) -> str:
        """Return the lightweight skill index for the LLM."""
        if not self.index:
            return ""
        lines = ["<available_skills>"]
        for s in self.index:
            lines.append(f"  [{s.id}] {s.name}: {s.summary}")
        lines.append("</available_skills>")
        return "\n".join(lines)

    def match_skills(self, query: str) -> list[SkillSummary]:
        """Simple keyword match — in prod, use embeddings."""
        query_lower = query.lower()
        matched = []
        for skill in self.index:
            score = 0
            for kw in skill.keywords:
                if kw.lower() in query_lower:
                    score += 1
            if skill.name.lower() in query_lower:
                score += 2
            if score > 0:
                matched.append((score, skill))
        matched.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in matched]

    def expand_skill(self, skill_id: str) -> str | None:
        """Load the full content of a matched skill (on-demand expansion)."""
        for skill in self.index:
            if skill.id == skill_id:
                if os.path.exists(skill.file_path):
                    with open(skill.file_path, "r") as f:
                        return f.read()
        return None

    def get_expanded_context(self, query: str) -> tuple[str, list[dict]]:
        """
        Progressive disclosure in action:
        1. Check index for matching skills
        2. Expand only the relevant ones
        3. Return the context block + metadata about what was loaded
        """
        matched = self.match_skills(query)
        if not matched:
            return "", []

        lines = ["<expanded_skills>"]
        loaded_skills = []
        for skill in matched[:3]:  # cap at 3 skills
            content = self.expand_skill(skill.id)
            if content:
                lines.append(f"  --- {skill.name} ---")
                lines.append(f"  {content}")
                loaded_skills.append({
                    "id": skill.id,
                    "name": skill.name,
                    "summary": skill.summary,
                    "loaded": True,
                })
        lines.append("</expanded_skills>")

        # Also note which skills were NOT loaded
        not_loaded = [
            {"id": s.id, "name": s.name, "summary": s.summary, "loaded": False}
            for s in self.index if s.id not in {ls["id"] for ls in loaded_skills}
        ]

        return "\n".join(lines), loaded_skills + not_loaded
