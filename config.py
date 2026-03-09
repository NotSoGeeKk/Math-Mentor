"""Central config — reads from .env via python-dotenv."""
import os
import time
from typing import Optional
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

load_dotenv()

# Gemini API
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
LLM_MODEL: str = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# RAG
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
KB_DIR: str = os.getenv("KB_DIR", "./rag/knowledge_base")
TOP_K_RETRIEVAL: int = int(os.getenv("TOP_K_RETRIEVAL", 5))

# Memory
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/memory.db")
MEMORY_TOP_K: int = int(os.getenv("MEMORY_TOP_K", 3))

# HITL
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

_gemini_client: Optional[genai.Client] = None


def validate_config() -> None:
    """Raise a clear error for missing required environment variables."""
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is not set. "
            "Copy .env.example to .env and set your Gemini API key."
        )


def get_gemini_client() -> genai.Client:
    """Return a singleton Gemini client configured with the API key."""
    global _gemini_client
    if _gemini_client is None:
        validate_config()
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    return _gemini_client


def call_gemini(*, model: str, contents, config_dict: Optional[dict] = None, max_retries: int = 4):
    """Call Gemini generate_content with automatic retry on rate-limit (429)."""
    client = get_gemini_client()
    kwargs = {"model": model, "contents": contents}
    if config_dict:
        kwargs["config"] = config_dict
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(**kwargs)
        except genai_errors.ClientError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                wait = 2 ** attempt
                time.sleep(wait)
                continue
            raise
