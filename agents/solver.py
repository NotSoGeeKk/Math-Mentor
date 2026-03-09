"""
Solver Agent
------------
Input : ParsedProblem + RoutingDecision + retrieved RAG chunks
Output: SolverResult dict
"""
from __future__ import annotations
import json
from typing import TypedDict
import config
from tools.calculator import evaluate

SYSTEM_PROMPT = """You are an expert JEE math solver. Be mathematically rigorous and precise.

Rules:
- Solve step-by-step. Each step must be self-contained and logically justified.
- Reference which formula or source you used (by source label) in each step.
- Use correct mathematical notation (^, sqrt, etc.).
- Double-check your arithmetic before writing the final answer.
- If a Python calculation would help verify the answer, provide the expression.
- Do NOT hallucinate formulas — only use what's in the provided context or standard JEE knowledge.

Respond ONLY with valid JSON:
{
  "solution_steps": ["Step 1: ...", "Step 2: ..."],
  "final_answer": "<clean final answer>",
  "confidence_score": 0.0,
  "sources_used": ["source_label_1"],
  "python_code_used": ""
}
"""


class SolverResult(TypedDict):
    solution_steps: list[str]
    final_answer: str
    confidence_score: float
    sources_used: list[str]
    python_code_used: str


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


def solve_problem(parsed: dict, routing: dict, rag_chunks: list[dict], memory_examples: list[dict]) -> SolverResult:
    """Solve a math problem using RAG context and memory examples."""
    context_block = "\n\n".join(
        f"[{c.get('source', 'doc')}]\n{c['text']}" for c in rag_chunks
    )
    memory_block = ""
    if memory_examples:
        memory_block = "\n\nSIMILAR SOLVED PROBLEMS (from memory):\n" + "\n\n".join(
            f"Q: {m['parsed_question']}\nA: {m['solution']}" for m in memory_examples
        )

    user_msg = f"""
PROBLEM:
{json.dumps(parsed, indent=2)}

STRATEGY:
{json.dumps(routing, indent=2)}

REFERENCE MATERIAL:
{context_block}
{memory_block}

Solve the problem now.
"""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{user_msg}",
        config_dict={"temperature": 0},
    )
    result = _parse_json_response(response.text)

    if routing.get("use_python_tool") and result.get("python_code_used"):
        calc = evaluate(result["python_code_used"])
        if calc["error"] is None:
            result["python_result"] = calc["result"]
        else:
            result["python_result_error"] = calc["error"]

    return result
