"""
Parser Agent
------------
Input : raw string (from OCR / ASR / text)
Output: ParsedProblem dict
"""
from __future__ import annotations
import json
from typing import TypedDict
import config

SYSTEM_PROMPT = """You are a math problem parser for JEE-level questions.
Given raw input (possibly noisy OCR or speech transcript), extract a clean structured representation.

Respond ONLY with valid JSON — no markdown fences, no commentary — matching this schema:
{
  "problem_text": "<cleaned problem statement>",
  "topic": "algebra | probability | calculus | linear_algebra | unknown",
  "variables": ["list", "of", "variables"],
  "constraints": ["list of constraints, e.g. x > 0"],
  "needs_clarification": false,
  "clarification_reason": ""
}

Set needs_clarification=true if the problem is ambiguous, incomplete, or contradictory.
"""


class ParsedProblem(TypedDict):
    problem_text: str
    topic: str
    variables: list[str]
    constraints: list[str]
    needs_clarification: bool
    clarification_reason: str


def _parse_json_response(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


def parse_problem(raw_input: str) -> ParsedProblem:
    """Parse raw input into a structured math problem."""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\nParse this input:\n\n{raw_input}",
        config_dict={"temperature": 0},
    )
    return _parse_json_response(response.text)
