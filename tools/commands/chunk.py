"""Command: chunk — Markdown -> chunks (one finding = one chunk)."""

from __future__ import annotations

from embeddings import chunker
from tools.commands._common import FINDINGS_DIR, timed


def run(_: str = "") -> None:
    with timed("Chunker"):
        chunks = chunker.chunk_directory()
        print(f"  markdown files: {len(list(FINDINGS_DIR.glob('*.md')))}")
        print(f"  chunks: {len(chunks)}")
        for c in chunks:
            print(f"    - {c['id']}")


COMMANDS = {"chunk": run}
