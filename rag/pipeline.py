"""
RAG Pipeline
------------
- Ingests markdown docs from KB_DIR into ChromaDB
- Provides retrieve() for top-k semantic search
- Uses Gemini embeddings via a custom ChromaDB embedding function
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


class GeminiEmbeddingFunction(EmbeddingFunction):
    """ChromaDB-compatible wrapper around the Gemini embedding API."""

    def __call__(self, input: Documents) -> Embeddings:
        client = config.get_gemini_client()
        result = client.models.embed_content(
            model=config.EMBEDDING_MODEL,
            contents=list(input),
        )
        return [list(e.values) for e in result.embeddings]


_client: Optional[chromadb.ClientAPI] = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        ef = GeminiEmbeddingFunction()
        _collection = _client.get_or_create_collection("knowledge_base", embedding_function=ef)
    return _collection


def ingest_knowledge_base(kb_dir: Optional[str] = None) -> int:
    """Chunk and embed all .md files in kb_dir. Returns number of chunks added."""
    kb_dir = kb_dir or config.KB_DIR
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    collection = _get_collection()

    docs, ids, metas = [], [], []
    for path in Path(kb_dir).glob("*.md"):
        text = path.read_text(encoding="utf-8")
        chunks = splitter.split_text(text)
        for i, chunk in enumerate(chunks):
            doc_id = f"{path.stem}_{i}"
            docs.append(chunk)
            ids.append(doc_id)
            metas.append({"source": path.name, "chunk_index": i})

    if docs:
        collection.upsert(documents=docs, ids=ids, metadatas=metas)

    return len(docs)


def retrieve(query: str, top_k: Optional[int] = None) -> list[dict]:
    """Return top-k relevant chunks for a query."""
    top_k = top_k or config.TOP_K_RETRIEVAL
    collection = _get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))

    chunks = []
    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": text,
            "source": meta.get("source", "unknown"),
            "score": round(1 - dist, 3),
        })
    return chunks
