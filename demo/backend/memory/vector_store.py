"""
Step 1 — Vector Store Integration (Milvus Lite)

Demonstrates:
  • Agent ↔ retriever tool ↔ vector DB
  • Upsert pipeline (ingest memories)
  • Query pipeline (retrieve + filter + rerank)
  • Formatting retrieved memories into a context block

Uses Milvus Lite — a single-file embedded vector DB that needs no server.
Same API as full Milvus, so you can swap to a cluster for production.

Schema uses Milvus auto-schema with dynamic fields:
  id (int, auto)  |  vector (768-d)  |  text, user_id, session_id, ... (dynamic)

Embeddings come from Gemini's text-embedding-004 model (768 dims).
"""

import os
import time
import uuid
from typing import Callable, Optional

from pymilvus import MilvusClient

COLLECTION = "agent_memories"
DIMENSION = 3072  # Gemini gemini-embedding-001 produces 3072-dim vectors


class VectorMemoryStore:
    """Semantic memory backed by Milvus Lite (swap for Milvus cluster in prod)."""

    def __init__(self, embed_fn: Callable[[str], list[float]], db_path: str = "./data/milvus_memories.db"):
        """
        Args:
            embed_fn: A function that takes a string and returns a 3072-d float vector.
            db_path:  Path for the Milvus Lite single-file DB.
        """
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.client = MilvusClient(db_path)
        if not self.client.has_collection(COLLECTION):
            self.client.create_collection(
                collection_name=COLLECTION,
                dimension=DIMENSION,
            )
        self.embed_fn = embed_fn

    # ── Upsert Pipeline ────────────────────────────────────────────────
    def upsert_memory(
        self,
        text: str,
        user_id: str,
        session_id: str,
        memory_type: str = "semantic",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Ingest a memory into the vector store."""
        mem_id = f"mem_{uuid.uuid4().hex[:12]}"
        vector = self.embed_fn(text)
        ts = time.time()

        row = {
            "id": hash(mem_id) & 0x7FFFFFFFFFFFFFFF,  # Milvus auto-schema uses int64 id
            "vector": vector,
            "text": text,
            "user_id": user_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "timestamp": ts,
            "mem_id": mem_id,
        }
        self.client.insert(collection_name=COLLECTION, data=[row])

        return {"id": mem_id, "text": text, "metadata": {
            "user_id": user_id, "session_id": session_id,
            "memory_type": memory_type, "timestamp": ts,
        }}

    # ── Query Pipeline (retrieve + filter + rerank) ────────────────────
    def retrieve_memories(
        self,
        query: str,
        user_id: str,
        top_k: int = 5,
        memory_type: Optional[str] = None,
        recency_weight: float = 0.3,
    ) -> list[dict]:
        """
        Retrieve relevant memories via semantic search, then re-rank
        with a recency bias so fresher memories bubble up.
        """
        query_vec = self.embed_fn(query)

        expr = f'user_id == "{user_id}"'
        if memory_type:
            expr += f' and memory_type == "{memory_type}"'

        results = self.client.search(
            collection_name=COLLECTION,
            data=[query_vec],
            limit=min(top_k * 2, 20),  # over-fetch for reranking
            filter=expr,
            output_fields=["text", "user_id", "session_id", "memory_type", "timestamp", "mem_id"],
        )

        if not results or not results[0]:
            return []

        now = time.time()
        scored = []
        for hit in results[0]:
            similarity = hit["distance"]
            ts = hit["entity"].get("timestamp", now)
            age_hours = (now - ts) / 3600

            # Recency boost: exponential decay (halves every 48h)
            recency_score = 2 ** (-age_hours / 48)
            combined = (1 - recency_weight) * similarity + recency_weight * recency_score

            scored.append({
                "id": hit["entity"].get("mem_id", str(hit["id"])),
                "text": hit["entity"]["text"],
                "metadata": {
                    "user_id": hit["entity"]["user_id"],
                    "session_id": hit["entity"]["session_id"],
                    "memory_type": hit["entity"]["memory_type"],
                    "timestamp": ts,
                },
                "similarity": round(similarity, 4),
                "recency_score": round(recency_score, 4),
                "combined_score": round(combined, 4),
            })

        scored.sort(key=lambda x: x["combined_score"], reverse=True)
        return scored[:top_k]

    # ── Format into context block ──────────────────────────────────────
    @staticmethod
    def format_context_block(memories: list[dict]) -> str:
        """Format retrieved memories into a context string for the LLM."""
        if not memories:
            return ""

        lines = ["<retrieved_memories>"]
        for i, mem in enumerate(memories, 1):
            score = mem["combined_score"]
            mtype = mem["metadata"].get("memory_type", "unknown")
            lines.append(f"  [{i}] (type={mtype}, relevance={score})")
            lines.append(f"      {mem['text']}")
        lines.append("</retrieved_memories>")
        return "\n".join(lines)

    # ── Housekeeping ───────────────────────────────────────────────────
    def delete_memories(self, user_id: str) -> int:
        """Delete all memories for a user (user-requested deletion)."""
        res = self.client.delete(
            collection_name=COLLECTION,
            filter=f'user_id == "{user_id}"',
        )
        return res.get("delete_count", 0) if isinstance(res, dict) else 0

    def get_all_memories(self, user_id: str) -> list[dict]:
        """Return every stored memory for a user (for the inspector panel)."""
        results = self.client.query(
            collection_name=COLLECTION,
            filter=f'user_id == "{user_id}"',
            output_fields=["mem_id", "text", "memory_type", "timestamp", "session_id"],
        )
        return [
            {
                "id": r.get("mem_id", str(r.get("id"))),
                "text": r["text"],
                "metadata": {
                    "memory_type": r["memory_type"],
                    "timestamp": r["timestamp"],
                    "session_id": r["session_id"],
                },
            }
            for r in results
        ]

    def count(self, user_id: str) -> int:
        results = self.client.query(
            collection_name=COLLECTION,
            filter=f'user_id == "{user_id}"',
            output_fields=["mem_id"],
        )
        return len(results)
