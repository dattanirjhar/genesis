"""Command: parser — raw scanner output -> Canonical JSON."""

from __future__ import annotations

from parser import parser as parser_mod
from tools.commands._common import NORMALIZED_DIR, RAW_DIR, timed


def run(_: str = "") -> None:
    with timed("Parser"):
        total = 0
        for src in [p for p in sorted(RAW_DIR.glob("*")) if p.is_file()]:
            try:
                doc = parser_mod.parse_file(src)
                parser_mod.parse_and_save(src)
                total += len(doc["findings"])
                print(f"  {src.name}: {doc['scan']['detected_tool']} -> "
                      f"{len(doc['findings'])} finding(s)")
            except Exception as exc:  # noqa: BLE001
                print(f"  {src.name}: skipped ({exc})")
        print(f"  => {total} findings -> {NORMALIZED_DIR}")


COMMANDS = {"parser": run}
