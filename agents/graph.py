"""
LangGraph Orchestration
-----------------------
Wires all agents into a state machine.

State flow:
  parse → route → rag_retrieve → memory_retrieve → solve → verify → explain
  
  Conditional edges:
  - parse      → HITL if needs_clarification
  - verify     → solve (retry, max 2) if not confident
  - verify     → HITL if hitl_required
"""
from __future__ import annotations
from typing import TypedDict, Optional, Annotated
import operator

from langgraph.graph import StateGraph, END

from agents.parser import parse_problem
from agents.router import route_problem
from agents.solver import solve_problem
from agents.verifier import verify_solution
from agents.explainer import explain_solution
from rag.pipeline import retrieve
from memory.store import get_similar_problems
import config

MAX_SOLVER_RETRIES = 2


# ── State schema ────────────────────────────────────────────────────────────

class GraphState(TypedDict):
    # Input
    raw_input: str
    input_type: str                  # "text" | "image" | "audio"

    # Agent outputs
    parsed: Optional[dict]
    routing: Optional[dict]
    rag_chunks: Optional[list]
    memory_examples: Optional[list]
    solution: Optional[dict]
    verification: Optional[dict]
    explanation: Optional[str]

    # Control
    hitl_required: bool
    hitl_reason: str
    solver_retries: int
    confidence_threshold: float

    # Trace (for UI)
    agent_trace: Annotated[list, operator.add]


# ── Node functions ───────────────────────────────────────────────────────────

def node_parse(state: GraphState) -> GraphState:
    parsed = parse_problem(state["raw_input"])
    trace = [{"agent": "Parser", "output": parsed}]
    hitl = parsed.get("needs_clarification", False)
    return {
        **state,
        "parsed": parsed,
        "hitl_required": hitl,
        "hitl_reason": parsed.get("clarification_reason", "") if hitl else "",
        "agent_trace": trace,
    }


def node_route(state: GraphState) -> GraphState:
    routing = route_problem(state["parsed"])
    return {**state, "routing": routing, "agent_trace": [{"agent": "Router", "output": routing}]}


def node_rag_retrieve(state: GraphState) -> GraphState:
    chunks = retrieve(state["parsed"]["problem_text"])
    return {**state, "rag_chunks": chunks, "agent_trace": [{"agent": "RAG Retriever", "output": f"{len(chunks)} chunks retrieved"}]}


def node_memory_retrieve(state: GraphState) -> GraphState:
    examples = get_similar_problems(state["parsed"]["problem_text"])
    return {**state, "memory_examples": examples, "agent_trace": [{"agent": "Memory Retriever", "output": f"{len(examples)} similar problems found"}]}


def node_solve(state: GraphState) -> GraphState:
    solution = solve_problem(
        state["parsed"],
        state["routing"],
        state["rag_chunks"] or [],
        state["memory_examples"] or [],
    )
    retries = state.get("solver_retries", 0)
    # Increment only for re-attempts (first solve remains retry count 0).
    if state.get("verification") is not None and not state["verification"].get("is_correct", False):
        retries += 1
    return {**state, "solution": solution, "solver_retries": retries, "agent_trace": [{"agent": "Solver", "output": solution}]}


def node_verify(state: GraphState) -> GraphState:
    verification = verify_solution(
        state["parsed"],
        state["solution"],
        confidence_threshold=state.get("confidence_threshold"),
    )
    hitl = verification.get("hitl_required", False)
    return {
        **state,
        "verification": verification,
        "hitl_required": hitl,
        "hitl_reason": verification.get("hitl_reason", "") if hitl else state.get("hitl_reason", ""),
        "agent_trace": [{"agent": "Verifier", "output": verification}],
    }


def node_explain(state: GraphState) -> GraphState:
    explanation = explain_solution(state["parsed"], state["solution"], state["verification"])
    return {**state, "explanation": explanation, "agent_trace": [{"agent": "Explainer", "output": explanation[:120] + "..."}]}


def node_hitl_pause(state: GraphState) -> GraphState:
    """Placeholder — real HITL is handled in Streamlit by checking hitl_required on state."""
    return {**state, "agent_trace": [{"agent": "HITL", "output": f"Paused: {state['hitl_reason']}"}]}


# ── Routing logic ────────────────────────────────────────────────────────────

def after_parse(state: GraphState) -> str:
    return "hitl" if state["hitl_required"] else "route"


def after_verify(state: GraphState) -> str:
    if state.get("hitl_required"):
        return "hitl"
    verification = state.get("verification") or {}
    if not verification.get("is_correct", True) and state.get("solver_retries", 0) < MAX_SOLVER_RETRIES:
        return "retry"
    return "explain"


# ── Graph assembly ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(GraphState)

    g.add_node("parse", node_parse)
    g.add_node("route", node_route)
    g.add_node("rag_retrieve", node_rag_retrieve)
    g.add_node("memory_retrieve", node_memory_retrieve)
    g.add_node("solve", node_solve)
    g.add_node("verify", node_verify)
    g.add_node("explain", node_explain)
    g.add_node("hitl", node_hitl_pause)

    g.set_entry_point("parse")
    g.add_conditional_edges("parse", after_parse, {"hitl": "hitl", "route": "route"})
    g.add_edge("route", "rag_retrieve")
    g.add_edge("rag_retrieve", "memory_retrieve")
    g.add_edge("memory_retrieve", "solve")
    g.add_conditional_edges("verify", after_verify, {"hitl": "hitl", "retry": "solve", "explain": "explain"})
    g.add_edge("solve", "verify")
    g.add_edge("explain", END)
    g.add_edge("hitl", END)

    return g.compile()


def run_graph(raw_input: str, input_type: str = "text", confidence_threshold: Optional[float] = None) -> GraphState:
    """Run the full agent graph and return final state."""
    graph = build_graph()
    initial_state: GraphState = {
        "raw_input": raw_input,
        "input_type": input_type,
        "parsed": None,
        "routing": None,
        "rag_chunks": None,
        "memory_examples": None,
        "solution": None,
        "verification": None,
        "explanation": None,
        "hitl_required": False,
        "hitl_reason": "",
        "solver_retries": 0,
        "confidence_threshold": confidence_threshold if confidence_threshold is not None else config.CONFIDENCE_THRESHOLD,
        "agent_trace": [],
    }
    return graph.invoke(initial_state)
