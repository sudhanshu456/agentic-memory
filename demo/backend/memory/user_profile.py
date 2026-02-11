"""
Step 3 — Cross-Session Persistence: User Profile Memory

Stores user preferences, constraints, and stable facts that persist
across every conversation session.
"""

import json
import os
import time
from typing import Optional


class UserProfileStore:
    """JSON-file-backed user profile store (swap for Postgres/Redis in prod)."""

    def __init__(self, data_dir: str = "./data/profiles"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _path(self, user_id: str) -> str:
        return os.path.join(self.data_dir, f"{user_id}.json")

    def get_profile(self, user_id: str) -> dict:
        path = self._path(user_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return self._default_profile(user_id)

    @staticmethod
    def _dedup_list(existing: list[str], new_items: list[str]) -> list[str]:
        """Deduplicate by checking normalized overlap (case-insensitive, substring)."""
        result = list(existing)
        for new in new_items:
            norm_new = new.lower().strip()
            is_dup = False
            for i, old in enumerate(result):
                norm_old = old.lower().strip()
                # Exact match after normalization
                if norm_new == norm_old:
                    is_dup = True
                    break
                # New is substring of existing or vice versa — keep the longer one
                if norm_new in norm_old:
                    is_dup = True
                    break
                if norm_old in norm_new:
                    result[i] = new  # replace with longer/more detailed version
                    is_dup = True
                    break
            if not is_dup:
                result.append(new)
        return result

    def update_profile(self, user_id: str, updates: dict) -> dict:
        """Merge updates into the existing profile with deduplication."""
        profile = self.get_profile(user_id)
        for key, value in updates.items():
            if key == "preferences" and isinstance(value, dict):
                profile.setdefault("preferences", {}).update(value)
            elif key == "constraints" and isinstance(value, list):
                profile["constraints"] = self._dedup_list(
                    profile.get("constraints", []), value
                )
            elif key == "facts" and isinstance(value, list):
                profile["facts"] = self._dedup_list(
                    profile.get("facts", []), value
                )
            else:
                profile[key] = value
        profile["updated_at"] = time.time()
        self._save(user_id, profile)
        return profile

    def format_profile_context(self, user_id: str) -> str:
        """Format profile into a context block for the LLM."""
        profile = self.get_profile(user_id)
        if not profile.get("preferences") and not profile.get("constraints") and not profile.get("facts"):
            return ""

        lines = ["<user_profile>"]
        if profile.get("name"):
            lines.append(f"  Name: {profile['name']}")
        if profile.get("preferences"):
            lines.append("  Preferences:")
            for k, v in profile["preferences"].items():
                lines.append(f"    - {k}: {v}")
        if profile.get("constraints"):
            lines.append("  Constraints:")
            for c in profile["constraints"]:
                lines.append(f"    - {c}")
        if profile.get("facts"):
            lines.append("  Known facts:")
            for f in profile["facts"]:
                lines.append(f"    - {f}")
        lines.append("</user_profile>")
        return "\n".join(lines)

    def _save(self, user_id: str, profile: dict):
        with open(self._path(user_id), "w") as f:
            json.dump(profile, f, indent=2)

    @staticmethod
    def _default_profile(user_id: str) -> dict:
        return {
            "user_id": user_id,
            "name": None,
            "preferences": {},
            "constraints": [],
            "facts": [],
            "created_at": time.time(),
            "updated_at": time.time(),
        }
