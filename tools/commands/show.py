"""
Command: show — one-glance pipeline status with a READY/STALE verdict.

Counts each stage's on-disk artifacts and reports whether the pipeline is fully
built and consistent, or which stage is stale.
"""

from __future__ import annotations

from config import COLLECTION_NAME, EMBED_MODEL, MODEL_NAME
from embeddings import chunker, index
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR, RAW_DIR

_LINE = "─" * 32


def _points() -> int:
    client = index.get_client()
    if client.collection_exists(COLLECTION_NAME):
        return client.get_collection(COLLECTION_NAME).points_count
    return 0


def _verdict(raw: int, normalized: int, knowledge: int, points: int) -> str:
    """Decide whether the pipeline is built and consistent, or where it's stale."""
    if raw == 0:
        return "EMPTY   (no raw scan files in data/raw)"
    if normalized == 0:
        return "STALE   (parser not run — try `parser` or `rebuild`)"
    if knowledge == 0:
        return "STALE   (knowledge not built — try `knowledge` or `rebuild`)"
    if points == 0:
        return "STALE   (not indexed — try `index` or `rebuild`)"
    if points != knowledge:
        return (f"STALE   (index out of date: {knowledge} knowledge vs "
                f"{points} points — run `rebuild`)")
    return "READY"


def run(_: str = "") -> None:
    raw = len([p for p in RAW_DIR.glob("*") if p.is_file()])
    normalized = len(list(NORMALIZED_DIR.glob("*.json")))
    knowledge = len(list(FINDINGS_DIR.glob("*.md")))
    chunks = len(chunker.chunk_directory())
    points = _points()

    print(f"\nPipeline Status\n{_LINE}")
    print(f"  Raw Files          {raw}")
    print(f"  Canonical JSON     {normalized}")
    print(f"  Knowledge Files    {knowledge}")
    print(f"  Chunks             {chunks}")
    print(f"  Vectors            {chunks}")
    print(f"  Qdrant             {points} points")
    print(f"  Embedding Model    {EMBED_MODEL.split('/')[-1]}")
    print(f"  Reasoning Model    {MODEL_NAME}")
    print(_LINE)
    print(f"  {_verdict(raw, normalized, knowledge, points)}")


COMMANDS = {"show": run}
