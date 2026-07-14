"""Command: clean — delete normalized JSON, knowledge Markdown, and the Qdrant index."""

from __future__ import annotations

import shutil
from pathlib import Path

from config import QDRANT_PATH
from embeddings import index
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR


def run(_: str = "") -> None:
    print("This deletes:")
    print(f"  {NORMALIZED_DIR}/*.json")
    print(f"  {FINDINGS_DIR}/*.md")
    print(f"  {QDRANT_PATH}/ (the whole Qdrant index)")
    try:
        confirm = input("Proceed? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "n"
    if confirm != "y":
        print("Aborted.")
        return

    for f in NORMALIZED_DIR.glob("*.json"):
        f.unlink()
    for f in FINDINGS_DIR.glob("*.md"):
        f.unlink()

    # Proper embedded-Qdrant shutdown: close the open file handle, THEN clear the
    # cached singleton, THEN delete. cache_clear() alone leaves the handle open.
    qpath = Path(QDRANT_PATH)
    print(f"Deleting Qdrant at: {qpath.resolve()}")
    client = index.get_client()
    client.close()
    index.get_client.cache_clear()
    if qpath.exists():
        shutil.rmtree(qpath)
    qpath.mkdir(parents=True, exist_ok=True)
    print("Cleaned. Run `rebuild` to regenerate.")


COMMANDS = {"clean": run}
