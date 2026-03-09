"""
Intent Router Agent
-------------------
Input : ParsedProblem
Output: RoutingDecision dict
"""
from __future__ import annotations
import json
from typing import TypedDict
import config

SYSTEM_PROMPT = """You are a math problem routing agent.
Given a structured math problem, decide the optimal solution strategy.

Respond ONLY with valid JSON:
{
  "topic_category": "algebra | probability | calculus | linear_algebra",
  "solution_strategy": "<brief description of approach>",
  "use_python_tool": true,
  "difficulty": "easy | medium | hard",
  "suggested_formulas": ["list of relevant formulas/theorems to look up"]
}
"""


class RoutingDecision(TypedDict):
    topic_category: str
    solution_strategy: str
    use_python_tool: bool
    difficulty: str
    suggested_formulas: list[str]


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


def route_problem(parsed: dict) -> RoutingDecision:
    """Classify and route a parsed problem."""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\nRoute this problem:\n\n{json.dumps(parsed, indent=2)}",
        config_dict={"temperature": 0},
    )
    return _parse_json_response(response.text)
