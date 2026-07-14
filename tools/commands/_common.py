"""
Shared helpers and directory constants for Genesis console commands.

Kept separate from genesis.py so command modules can import helpers without a
circular dependency on the dispatcher.
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path

from config import KNOWLEDGE_DIR, NORMALIZED_DIR, RAW_DIR
from embeddings import chunker

# Pipeline directories come straight from config (single source of truth).
FINDINGS_DIR = KNOWLEDGE_DIR


@contextmanager
def timed(label: str):
    """Print a titled block and its wall-clock time."""
    print(f"\n{label}\n{'-' * len(label)}")
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"Time: {time.perf_counter() - start:.2f} sec")


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def summary_line(markdown: str) -> str:
    """Return the first line of the ## Summary section, for compact previews."""
    lines = markdown.splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower() == "## summary":
            for nxt in lines[i + 1:]:
                if nxt.strip():
                    return nxt.strip()
            break
    return ""


def find_chunk(finding_id: str) -> dict | None:
    for chunk in chunker.chunk_directory():
        if chunk["id"] == finding_id:
            return chunk
    return None


def print_hits(hits: list[dict]) -> None:
    if not hits:
        print("(nothing indexed, or no matches)")
        return
    for rank, h in enumerate(hits, 1):
        print(f"\nRank {rank}  |  score {h.get('score', 0):.3f}")
        print(f"  finding : {h.get('finding_id')}")
        print(f"  host    : {h.get('host')}   service: {h.get('service')}   "
              f"severity: {h.get('severity')}")
        summary = summary_line(h.get("text", ""))
        if summary:
            print(f"  summary : {summary}")
