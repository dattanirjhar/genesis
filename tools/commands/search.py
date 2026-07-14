"""Command: search — semantic retrieval only (no LLM)."""

from __future__ import annotations

from config import TOP_K
from embeddings import search as vsearch
from tools.commands._common import print_hits


def run(arg: str) -> None:
    if not arg:
        print("  usage: search <text>")
        return
    print_hits(vsearch.search(arg, top_k=TOP_K))


COMMANDS = {"search": run}
