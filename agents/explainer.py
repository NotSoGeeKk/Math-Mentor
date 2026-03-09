"""
Explainer / Tutor Agent
-----------------------
Input : ParsedProblem + SolverResult + VerifierResult
Output: Explanation string (student-friendly, well-formatted markdown)
"""
from __future__ import annotations
import config

SYSTEM_PROMPT = """You are a JEE math tutor producing clean, accurate, well-formatted explanations.

FORMAT YOUR RESPONSE EXACTLY LIKE THIS (use markdown):

#### Key Concept
> State the one core formula or theorem used, written in plain math notation.

#### Step-by-Step Solution

1. **[Short title]** — Explanation of this step with the math.
2. **[Short title]** — Next step.
(continue as needed)

#### Final Answer
State the final answer clearly.

#### Common Pitfall
> One practical mistake students make on this type of problem.

RULES:
- Be concise: max 300 words total.
- Use plain math notation (x^2, sqrt(x), dy/dx) not LaTeX.
- Each step must be ONE numbered item — don't nest sub-bullets.
- Bold the step title, then use a dash to explain.
- Do NOT add any greeting, filler, or motivational text.
- Do NOT repeat the problem statement.
- Be mathematically precise — every step must be logically justified.
"""


def explain_solution(parsed: dict, solver_result: dict, verifier_result: dict) -> str:
    """Generate a student-friendly explanation."""
    steps = solver_result.get("solution_steps", [])
    issues = verifier_result.get("issues", [])
    sources = solver_result.get("sources_used", [])
    user_msg = f"""PROBLEM: {parsed.get('problem_text', '')}
TOPIC: {parsed.get('topic', 'unknown')}

SOLUTION STEPS:
{chr(10).join(steps)}

FINAL ANSWER: {solver_result.get('final_answer', '')}

SOURCES USED: {', '.join(sources) or 'None'}
VERIFIER NOTES: {', '.join(issues) or 'None'}

Write the explanation now. Follow the format exactly."""
    response = config.call_gemini(
        model=config.LLM_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{user_msg}",
        config_dict={"temperature": 0.2},
    )
    return response.text
