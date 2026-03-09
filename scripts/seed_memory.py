"""Seed local memory store with a tiny demo record."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.store import save_attempt, update_feedback  # noqa: E402


def main() -> None:
    row_id = save_attempt(
        input_type="text",
        raw_input="Differentiate x^3 sin(x).",
        parsed={
            "problem_text": "Differentiate x^3 sin(x).",
            "topic": "calculus",
            "variables": ["x"],
            "constraints": [],
            "needs_clarification": False,
            "clarification_reason": "",
        },
        rag_chunks=[{"source": "calculus_basics.md", "text": "Use product rule: (uv)' = u'v + uv'."}],
        solution={
            "solution_steps": [
                "Let u=x^3 and v=sin(x).",
                "Apply product rule: d/dx[x^3 sin(x)] = 3x^2 sin(x) + x^3 cos(x).",
            ],
            "final_answer": "3x^2 sin(x) + x^3 cos(x)",
            "confidence_score": 0.95,
            "sources_used": ["calculus_basics.md"],
            "python_code_used": "",
        },
        verification={
            "is_correct": True,
            "confidence": 0.95,
            "issues": [],
            "hitl_required": False,
            "hitl_reason": "",
        },
    )
    update_feedback(row_id, "correct", "Seeded demo sample.")
    print(f"Seeded memory with row_id={row_id}")


if __name__ == "__main__":
    main()
