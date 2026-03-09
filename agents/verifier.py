"""
Verifier / Critic Agent
-----------------------
Input : ParsedProblem + SolverResult
Output: VerifierResult dict
"""
from __future__ import annotations
import json
from typing import Optional, TypedDict
import config

SYSTEM_PROMPT = """You are a rigorous math verifier for JEE-level problems.
Given a problem and a proposed solution, critically evaluate it.

Check:
1. Mathematical correctness (re-derive or sanity-check key steps)
2. Domain constraints (e.g. sqrt of negative, division by zero, log of negative)
3. Units and dimensional consistency
4. Edge cases mentioned in the problem

Respond ONLY with valid JSON:
{
  "is_correct": true,
  "confidence": 0.0,
  "issues": ["list of issues found, empty if none"],
  "hitl_required": false,
  "hitl_reason": ""
}

Set hitl_required=true if confidence < 0.7 or critical issues found.
"""


class VerifierResult(TypedDict):
    is_correct: bool
    confidence: float
    issues: list[str]
    hitl_required: bool
    hitl_reason: str


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


def verify_solution(parsed: dict, solver_result: dict, confidence_threshold: Optional[float] = None) -> VerifierResult:
    """Verify a proposed solution."""
    threshold = config.CONFIDENCE_THRESHOLD if confidence_threshold is None else confidence_threshold
    user_msg = f"""
PROBLEM:
{json.dumps(parsed, indent=2)}

PROPOSED SOLUTION:
{json.dumps(solver_result, indent=2)}

Verify this solution.
"""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{user_msg}",
        config_dict={"temperature": 0},
    )
    result = _parse_json_response(response.text)
    if result.get("confidence", 0.0) < threshold and not result.get("hitl_required", False):
        result["hitl_required"] = True
        result["hitl_reason"] = f"Low verifier confidence (< {threshold:.2f})"
    return result
