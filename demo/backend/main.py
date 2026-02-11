"""
OpsAgent Demo — FastAPI Backend

Endpoints:
  POST /chat                              Send a message, get response + memory debug info
  GET  /memory/{user_id}                  Inspect all stored memories, profile, sessions
  POST /sessions                          Create a new session
  GET  /sessions/{user_id}                List sessions for a user
  GET  /sessions/{user_id}/{session_id}   Get full session with messages
  DELETE /sessions/{user_id}              Delete ALL sessions for a user
  DELETE /sessions/{user_id}/{session_id} Delete a single session
  DELETE /memory/{user_id}                Wipe all memories for a user (reset demo)
"""

import os
import uuid
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai

from agent import OpsAgent

load_dotenv()
logging.basicConfig(level=logging.INFO)

# ── Gemini client ──────────────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not set. Copy .env.example → .env and add your key.")

gemini_client = genai.Client(api_key=api_key)

# ── Agent singleton ────────────────────────────────────────────────────
agent = OpsAgent(gemini_client)

# ── FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(title="OpsAgent — Agentic Memory Demo", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────
class ChatRequest(BaseModel):
    user_id: str = "sre-demo-user"
    session_id: str | None = None
    message: str


class SessionRequest(BaseModel):
    user_id: str = "sre-demo-user"


# ── Endpoints ─────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    # Ensure session exists
    if not agent.session_store.get_session(req.user_id, session_id):
        agent.session_store.create_session(req.user_id, session_id)

    result = await agent.chat(req.user_id, session_id, req.message)
    return {
        "session_id": session_id,
        "response": result["response"],
        "debug": result["debug"],
    }


@app.get("/memory/{user_id}")
async def get_memory(user_id: str):
    return agent.get_memory_stats(user_id)


@app.get("/sessions/{user_id}")
async def list_sessions(user_id: str):
    sessions = agent.session_store.list_sessions(user_id)
    detailed = []
    for s in sessions:
        full = agent.session_store.get_session(user_id, s["session_id"])
        detailed.append({
            "session_id": s["session_id"],
            "created_at": s.get("created_at"),
            "message_count": len(full["messages"]) if full else 0,
            "summary": full.get("summary") if full else None,
        })
    return detailed


@app.post("/sessions")
async def create_session(req: SessionRequest):
    session_id = str(uuid.uuid4())
    agent.session_store.create_session(req.user_id, session_id)
    return {"session_id": session_id, "user_id": req.user_id}


@app.get("/sessions/{user_id}/{session_id}")
async def get_session(user_id: str, session_id: str):
    session = agent.session_store.get_session(user_id, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/sessions/{user_id}/{session_id}")
async def delete_session(user_id: str, session_id: str):
    path = agent.session_store._path(user_id, session_id)
    if os.path.exists(path):
        os.remove(path)
    # Remove from index
    sessions = agent.session_store.list_sessions(user_id)
    sessions = [s for s in sessions if s["session_id"] != session_id]
    import json
    with open(agent.session_store._index_path(user_id), "w") as f:
        json.dump(sessions, f, indent=2)
    return {"deleted": session_id}


@app.delete("/sessions/{user_id}")
async def delete_all_sessions(user_id: str):
    import shutil
    user_dir = os.path.join(agent.session_store.data_dir, user_id)
    if os.path.isdir(user_dir):
        shutil.rmtree(user_dir)
    return {"deleted_all": True}


@app.delete("/memory/{user_id}")
async def reset_memory(user_id: str):
    deleted = agent.vector_store.delete_memories(user_id)
    # Reset profile
    profile_path = agent.profile_store._path(user_id)
    if os.path.exists(profile_path):
        os.remove(profile_path)
    return {"deleted_memories": deleted, "profile_reset": True}


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "OpsAgent", "model": agent.model}
