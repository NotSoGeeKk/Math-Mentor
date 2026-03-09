"""
ASR Tool
--------
Transcribes audio using Gemini's multimodal capabilities.
Post-processes math-specific spoken phrases.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Union

from google.genai import types
import config

MATH_PHRASE_MAP = [
    (r"\bsquare root of\b", "sqrt("),
    (r"\bcube root of\b", "cbrt("),
    (r"\braised to\b", "^"),
    (r"\bto the power of\b", "^"),
    (r"\bdivided by\b", "/"),
    (r"\btimes\b", "*"),
    (r"\bpi\b", "pi"),
    (r"\binfinity\b", "inf"),
    (r"\btheta\b", "theta"),
    (r"\balpha\b", "alpha"),
    (r"\bbeta\b", "beta"),
    (r"\bdelta\b", "delta"),
    (r"\bsigma\b", "sigma"),
    (r"\blambda\b", "lambda"),
]

TRANSCRIPTION_PROMPT = """Transcribe the spoken audio exactly. The audio contains a math problem.
Pay special attention to mathematical terms and notation.
Return ONLY the transcription — no commentary."""

MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
}


def _postprocess(text: str) -> str:
    for pattern, replacement in MATH_PHRASE_MAP:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _call_gemini_audio(audio_bytes: bytes, mime_type: str) -> dict:
    """Send audio bytes to Gemini and return transcription."""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            types.Part.from_text(text=TRANSCRIPTION_PROMPT),
        ],
    )
    raw = (response.text or "").strip()
    processed = _postprocess(raw)
    low_confidence = len(raw.split()) < 3
    return {
        "raw_transcript": raw,
        "processed_transcript": processed,
        "low_confidence": low_confidence,
    }


def transcribe_audio(audio_path: Union[str, Path]) -> dict:
    """Transcribe audio file to text."""
    audio_path = Path(audio_path)
    audio_bytes = audio_path.read_bytes()
    ext = audio_path.suffix.lower()
    mime_type = MIME_MAP.get(ext, "audio/mpeg")
    return _call_gemini_audio(audio_bytes, mime_type)


def transcribe_bytes(audio_bytes: bytes, filename: str = "audio.mp3") -> dict:
    """Transcribe audio bytes (for Streamlit uploads)."""
    ext = Path(filename).suffix.lower()
    mime_type = MIME_MAP.get(ext, "audio/mpeg")
    return _call_gemini_audio(audio_bytes, mime_type)
