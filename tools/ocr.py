"""
OCR Tool
--------
Uses Gemini Vision to extract math problems from images.
Returns extracted text + a low-confidence flag for HITL.
"""
from __future__ import annotations
from pathlib import Path
from typing import Union

from google.genai import types
import config

EXTRACTION_PROMPT = """Extract the math problem from this image exactly as written.
Return ONLY the problem text — no commentary, no formatting, no explanation.
If the image is unclear or you cannot confidently read it, start your response with [LOW_CONFIDENCE]."""


def _call_gemini_vision(image_bytes: bytes, media_type: str) -> dict:
    """Send image bytes to Gemini and parse the extraction response."""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            types.Part.from_text(text=EXTRACTION_PROMPT),
        ],
    )
    text = (response.text or "").strip()
    low_confidence = text.startswith("[LOW_CONFIDENCE]")
    clean_text = text.removeprefix("[LOW_CONFIDENCE]").strip()
    return {"extracted_text": clean_text, "low_confidence": low_confidence}


def extract_from_image(image_path: Union[str, Path]) -> dict:
    """Extract math problem text from an image file."""
    image_bytes = Path(image_path).read_bytes()
    ext = Path(image_path).suffix.lstrip(".").lower()
    media_type = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return _call_gemini_vision(image_bytes, media_type)


def extract_from_bytes(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    """Extract math problem text from raw bytes (for Streamlit uploads)."""
    return _call_gemini_vision(image_bytes, media_type)
