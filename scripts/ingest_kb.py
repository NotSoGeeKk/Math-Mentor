"""Standalone script to ingest the knowledge base into ChromaDB."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from rag.pipeline import ingest_knowledge_base

if __name__ == "__main__":
    n = ingest_knowledge_base()
    print(f"✅ Ingested {n} chunks")
