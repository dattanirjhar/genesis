"""
Command: reason — retrieval + reasoning, showing the exact context first.

Retrieval runs, the exact context string bound for the model is printed, then
after [ENTER] the reasoner is called on those same hits (no second search). This
makes a bad answer traceable to retrieval or to the LLM.
"""

from __future__ import annotations

from config import TOP_K
from embeddings import search as vsearch
from llm import reasoner
from llm.client import chat
from tools.commands._common import print_hits


def run(arg: str) -> None:
    if not arg:
        try:
            arg = input("  Question > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not arg:
            return

    hits = vsearch.search(arg, top_k=TOP_K)
    print("\n--- Retrieval (before the LLM) ---")
    print_hits(hits)
    if not hits:
        return

    context = reasoner.build_context(hits)
    print("\n--- Exact context passed to the reasoner ---")
    print(context)

    try:
        input("\n[ENTER] to run the reasoner (or Ctrl-C to skip) ...")
    except (EOFError, KeyboardInterrupt):
        print()
        return

    print("\nCalling reasoner ...")
    answer = chat(prompt=f"CONTEXT:\n{context}\n\nQUESTION:\n{arg}", task="reasoning")
    print("\n=== GROUNDED ANSWER ===")
    print(answer)


COMMANDS = {"reason": run}
