"""
Command: status — where the current engagement stands in the pipeline.

    Genesis> status

The quickest way to see where you are while iterating on scans: the last target,
raw/parsed/knowledge/vector counts, when you last scanned, and whether the
reasoner is up.
"""

from __future__ import annotations

import json

from config import (
    COLLECTION_NAME,
    EXECUTION_DIR,
    KNOWLEDGE_DIR,
    NORMALIZED_DIR,
    RAW_DIR,
)
from embeddings import index
from llm.client import is_available


def _last_scan() -> tuple[str | None, str | None]:
    """Target and finish time of the most recent execution log."""
    logs = sorted(EXECUTION_DIR.glob("scan_*.json"))
    if not logs:
        return None, None
    try:
        rec = json.loads(logs[-1].read_text())
        return rec.get("target"), rec.get("finished")
    except (ValueError, OSError):
        return None, None


def _parsed_findings() -> int:
    total = 0
    for doc in NORMALIZED_DIR.glob("*.json"):
        try:
            total += len(json.loads(doc.read_text()).get("findings", []))
        except (ValueError, OSError):
            pass
    return total


def run(_: str = "") -> None:
    target, last = _last_scan()
    raw = len([p for p in RAW_DIR.glob("*") if p.is_file()])
    knowledge = len(list(KNOWLEDGE_DIR.glob("*.md")))

    client = index.get_client()
    vectors = (client.get_collection(COLLECTION_NAME).points_count
               if client.collection_exists(COLLECTION_NAME) else 0)

    parsed = _parsed_findings()
    state = ("empty" if raw == 0 else
             "scanned (not ingested)" if knowledge == 0 else
             "stale (re-ingest)" if vectors != knowledge else
             "ready")

    print("\nCurrent engagement\n------------------")
    print(f"  Target:          {target or '(none — run scan)'}")
    print(f"  Scan state:      {state}")
    print(f"  Raw files:       {raw}")
    print(f"  Parsed findings: {parsed}")
    print(f"  Knowledge:       {knowledge} markdown")
    print(f"  Vectors:         {vectors}")
    print(f"  Collection:      {COLLECTION_NAME}")
    print(f"  Last scan:       {last or '(none)'}")
    print(f"  Reasoner:        {'READY' if is_available() else 'DOWN (run: ollama serve)'}")


COMMANDS = {"status": run}
