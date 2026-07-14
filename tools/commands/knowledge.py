"""Command: knowledge — Canonical JSON -> Markdown (one LLM call per finding)."""

from __future__ import annotations

from llm import knowledge_builder as kb
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR, timed


def run(_: str = "") -> None:
    with timed("Knowledge Builder"):
        docs = sorted(NORMALIZED_DIR.glob("*.json"))
        if not docs:
            print("  No normalized JSON. Run `parser` first.")
            return
        written = failed = 0
        for doc_path in docs:
            summary = kb.process_document(doc_path)
            written += len(summary["written"])
            failed += len(summary["failed"])
        print(f"  => {written} markdown file(s), {failed} failed -> {FINDINGS_DIR}")


COMMANDS = {"knowledge": run}
