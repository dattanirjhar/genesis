"""Command: clean — reset the current engagement (raw, knowledge, vectors, target)."""

from __future__ import annotations

import shutil
from pathlib import Path

from config import EXECUTION_DIR, QDRANT_PATH
from embeddings import index
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR, RAW_DIR


def run(_: str = "") -> None:
    print("This resets the current engagement and deletes:")
    print(f"  {RAW_DIR}/           (all raw scan files)")
    print(f"  {NORMALIZED_DIR}/    (canonical JSON)")
    print(f"  {FINDINGS_DIR}/      (knowledge markdown)")
    print(f"  {QDRANT_PATH}/       (the vector index)")
    print(f"  {EXECUTION_DIR}/     (scan logs — clears the target/last-scan)")
    print("  (reports in knowledge/reports/ are kept)")
    try:
        confirm = input("Proceed? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "n"
    if confirm != "y":
        print("Aborted.")
        return

    # All raw files (not just *.json — scans are .xml/.jsonl/.log/.txt too).
    for f in RAW_DIR.glob("*"):
        if f.is_file():
            f.unlink()
    for f in NORMALIZED_DIR.glob("*.json"):
        f.unlink()
    for f in FINDINGS_DIR.glob("*.md"):
        f.unlink()
    # Execution logs hold the engagement target + last-scan time, so status
    # keeps showing the old target until these are gone.
    for f in EXECUTION_DIR.glob("scan_*.json"):
        f.unlink()

    # Proper embedded-Qdrant shutdown: close the open handle, clear the cached
    # singleton, THEN delete. cache_clear() alone leaves the handle open.
    qpath = Path(QDRANT_PATH)
    print(f"Deleting Qdrant at: {qpath.resolve()}")
    index.get_client().close()
    index.get_client.cache_clear()
    if qpath.exists():
        shutil.rmtree(qpath)
    qpath.mkdir(parents=True, exist_ok=True)

    print("Cleaned. Engagement reset — scan a new target with `run <target>`.")


COMMANDS = {"clean": run}
