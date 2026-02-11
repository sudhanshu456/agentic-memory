"""
Step 3 — Cross-Session Persistence: Session Store

Manages chat history, episodic memory, and rolling summaries per session.
Provides the "last time we..." continuity and cold-start context injection.
"""

import json
import os
import time
from typing import Optional


class SessionStore:
    """JSON-file-backed session store (swap for SQLite/Postgres in prod)."""

    def __init__(self, data_dir: str = "./data/sessions"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _path(self, user_id: str, session_id: str) -> str:
        user_dir = os.path.join(self.data_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, f"{session_id}.json")

    def _index_path(self, user_id: str) -> str:
        user_dir = os.path.join(self.data_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return os.path.join(user_dir, "_index.json")

    # ── Session CRUD ───────────────────────────────────────────────────
    def create_session(self, user_id: str, session_id: str) -> dict:
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "title": "New session",
            "messages": [],
            "summary": None,
            "created_at": time.time(),
            "updated_at": time.time(),
        }
        self._save_session(user_id, session_id, session)
        self._update_index(user_id, session_id)
        return session

    def get_session(self, user_id: str, session_id: str) -> Optional[dict]:
        path = self._path(user_id, session_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

    def add_message(self, user_id: str, session_id: str, role: str, content: str) -> dict:
        session = self.get_session(user_id, session_id)
        if not session:
            session = self.create_session(user_id, session_id)
        session["messages"].append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        # Auto-title from first user message
        if role == "user" and session.get("title") == "New session":
            session["title"] = content[:60].strip() + ("..." if len(content) > 60 else "")
        session["updated_at"] = time.time()
        self._save_session(user_id, session_id, session)
        self._refresh_index(user_id, session_id, session)
        return session

    def set_summary(self, user_id: str, session_id: str, summary: str):
        session = self.get_session(user_id, session_id)
        if session:
            session["summary"] = summary
            session["updated_at"] = time.time()
            self._save_session(user_id, session_id, session)

    # ── Cross-Session: list past sessions ──────────────────────────────
    def list_sessions(self, user_id: str) -> list[dict]:
        idx_path = self._index_path(user_id)
        if os.path.exists(idx_path):
            with open(idx_path, "r") as f:
                return json.load(f)
        return []

    def get_previous_session_summary(self, user_id: str, current_session_id: str) -> Optional[str]:
        """Cold-start: get the summary of the most recent *other* session."""
        sessions = self.list_sessions(user_id)
        for s in reversed(sessions):
            if s["session_id"] != current_session_id:
                prev = self.get_session(user_id, s["session_id"])
                if prev and prev.get("summary"):
                    return prev["summary"]
        return None

    def format_episodic_context(self, user_id: str, current_session_id: str) -> str:
        """Build an episodic context block from the previous session."""
        summary = self.get_previous_session_summary(user_id, current_session_id)
        if not summary:
            return ""
        return f"<episodic_memory>\n  Last session summary: {summary}\n</episodic_memory>"

    # ── Internals ──────────────────────────────────────────────────────
    def _save_session(self, user_id: str, session_id: str, session: dict):
        with open(self._path(user_id, session_id), "w") as f:
            json.dump(session, f, indent=2)

    def _update_index(self, user_id: str, session_id: str):
        sessions = self.list_sessions(user_id)
        if not any(s["session_id"] == session_id for s in sessions):
            sessions.append({
                "session_id": session_id,
                "title": "New session",
                "message_count": 0,
                "created_at": time.time(),
            })
            with open(self._index_path(user_id), "w") as f:
                json.dump(sessions, f, indent=2)

    def _refresh_index(self, user_id: str, session_id: str, session: dict):
        """Update index entry with current title and message count."""
        sessions = self.list_sessions(user_id)
        for s in sessions:
            if s["session_id"] == session_id:
                s["title"] = session.get("title", "New session")
                s["message_count"] = len(session.get("messages", []))
                s["summary"] = session.get("summary") is not None
                break
        with open(self._index_path(user_id), "w") as f:
            json.dump(sessions, f, indent=2)
