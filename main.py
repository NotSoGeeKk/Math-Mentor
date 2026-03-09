"""
CLI entrypoint for Math Mentor.
Usage:
  python main.py "Find the derivative of x^3 sin(x)"
  python main.py --ingest-kb         # ingest knowledge base into ChromaDB
"""
import sys
import argparse
from agents.graph import run_graph
from rag.pipeline import ingest_knowledge_base
import config


def main():
    try:
        config.validate_config()
    except RuntimeError as exc:
        print(f"❌ {exc}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Math Mentor CLI")
    parser.add_argument("problem", nargs="?", help="Math problem to solve")
    parser.add_argument("--ingest-kb", action="store_true", help="Ingest knowledge base")
    args = parser.parse_args()

    if args.ingest_kb:
        n = ingest_knowledge_base()
        print(f"✅ Ingested {n} chunks into ChromaDB")
        return

    if not args.problem:
        parser.print_help()
        sys.exit(1)

    print(f"\n🧮 Solving: {args.problem}\n{'─' * 50}")
    state = run_graph(args.problem, input_type="text")

    if state.get("hitl_required"):
        print(f"⚠️  HITL required: {state['hitl_reason']}")
    if state.get("explanation"):
        print("\n📖 Explanation:\n")
        print(state["explanation"])
    if state.get("solution"):
        print(f"\n✅ Answer: {state['solution']['final_answer']}")


if __name__ == "__main__":
    main()
