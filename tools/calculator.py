"""
Python Calculator Tool
----------------------
Safe math expression evaluator for the Solver Agent.
Uses a restricted exec environment — no builtins, only math/numpy.
"""
from __future__ import annotations
import math
import traceback

_SAFE_GLOBALS = {
    "__builtins__": {},
    "math": math,
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "abs": abs,
    "round": round,
    "pow": pow,
    "sum": sum,
    "min": min,
    "max": max,
}


def evaluate(expression: str) -> dict:
    """Safely evaluate a math expression string."""
    try:
        result = eval(expression, _SAFE_GLOBALS, {})  # noqa: S307
        return {"result": result, "error": None}
    except Exception:
        return {"result": None, "error": traceback.format_exc(limit=1)}
