"""
Memory Store
------------
SQLite (via SQLAlchemy) for full problem records.
ChromaDB collection for semantic similarity search on past problems.
Uses Gemini embeddings.
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, Session

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

import config

os.makedirs(os.path.dirname(config.SQLITE_DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{config.SQLITE_DB_PATH}")


class Base(DeclarativeBase):
    pass


class SolvedProblem(Base):
    __tablename__ = "solved_problems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    input_type = Column(String(20))          # text | image | audio
    raw_input = Column(Text)
    parsed_question = Column(Text)
    retrieved_docs = Column(Text)            # JSON string
    solution = Column(Text)                  # JSON string
    verifier_outcome = Column(Text)          # JSON string
    verifier_confidence = Column(Float)
    user_feedback = Column(String(20))       # correct | incorrect | pending
    feedback_comment = Column(Text)


Base.metadata.create_all(engine)


class GeminiEmbeddingFunction(EmbeddingFunction):
    """ChromaDB-compatible wrapper around the Gemini embedding API."""

    def __call__(self, input: Documents) -> Embeddings:
        client = config.get_gemini_client()
        result = client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=list(input),
        )
        return [list(e.values) for e in result.embeddings]


# ── ChromaDB for similarity search ──────────────────────────────────────────

_mem_collection = None


def _get_mem_collection():
    global _mem_collection
    if _mem_collection is None:
        os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
        client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        ef = GeminiEmbeddingFunction()
        _mem_collection = client.get_or_create_collection("solved_problems", embedding_function=ef)
    return _mem_collection


# ── Public API ───────────────────────────────────────────────────────────────

def save_attempt(
    input_type: str,
    raw_input: str,
    parsed: dict,
    rag_chunks: list,
    solution: dict,
    verification: dict,
) -> int:
    """Persist a solving attempt. Returns the new row ID."""
    with Session(engine) as session:
        row = SolvedProblem(
            input_type=input_type,
            raw_input=raw_input,
            parsed_question=parsed.get("problem_text", ""),
            retrieved_docs=json.dumps(rag_chunks),
            solution=json.dumps(solution),
            verifier_outcome=json.dumps(verification),
            verifier_confidence=verification.get("confidence", 0.0),
            user_feedback="pending",
        )
        session.add(row)
        session.commit()
        row_id = row.id

    col = _get_mem_collection()
    col.upsert(
        documents=[parsed.get("problem_text", raw_input)],
        ids=[str(row_id)],
        metadatas=[{"solution": json.dumps(solution), "feedback": "pending"}],
    )
    return row_id


def update_feedback(row_id: int, feedback: str, comment: str = "") -> None:
    """Update user feedback for a solved problem."""
    with Session(engine) as session:
        row = session.get(SolvedProblem, row_id)
        if row:
            row.user_feedback = feedback
            row.feedback_comment = comment
            session.commit()

    col = _get_mem_collection()
    existing = col.get(ids=[str(row_id)], include=["documents", "metadatas"])
    if not existing.get("ids"):
        return
    documents = existing.get("documents") or [""]
    metadatas = existing.get("metadatas") or [{}]
    document = documents[0] if documents else ""
    metadata = metadatas[0] if metadatas else {}
    metadata = metadata or {}
    metadata["feedback"] = feedback
    col.upsert(
        documents=[document],
        ids=[str(row_id)],
        metadatas=[metadata],
    )


def get_similar_problems(query: str, top_k: Optional[int] = None) -> list[dict]:
    """Return similar previously solved problems for few-shot prompting."""
    top_k = top_k or config.MEMORY_TOP_K
    col = _get_mem_collection()
    if col.count() == 0:
        return []

    results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
    examples = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        if meta.get("feedback") == "incorrect":
            continue
        examples.append({
            "parsed_question": doc,
            "solution": meta.get("solution", ""),
        })
    return examples
