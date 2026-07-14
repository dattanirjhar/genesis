"""
Parser — the dispatcher that turns any raw scan file into Canonical JSON.

The prototype does not care how a scan was produced. It cares only about
consuming outputs. So this module is a thin coordinator:

    raw file  ->  detector (which tool?)  ->  tool parser  ->  Canonical JSON

It delegates detection to detector.py and the schema to canonical.py, and owns
only the file-level flow: read a raw file, route it, persist the result. Adding
a scanner means adding a module under parser/parsers/ and an entry in
detector.PARSER_ORDER — nothing here changes, because everything downstream
depends on the Canonical JSON contract, not on any scanner's native format.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.detector import detect_tool

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "normalized"


def parse_file(path: str | Path) -> dict:
    """Detect the tool for one file and return its Canonical JSON document."""
    path = Path(path)
    name, module = detect_tool(path)
    doc = module.parse(path)
    doc["scan"]["detected_tool"] = name
    return doc


def normalized_path(src: str | Path) -> Path:
    """Where the Canonical JSON for a given raw file is written."""
    return OUT_DIR / f"{Path(src).stem}.json"


def parse_and_save(path: str | Path) -> Path:
    """Parse one raw file and write its Canonical JSON to data/normalized/."""
    doc = parse_file(path)
    out = normalized_path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return out


def parse_dir(raw_dir: str | Path = RAW_DIR) -> list[Path]:
    """Parse every file in a directory. Skips files no parser recognizes."""
    outputs = []
    for src in sorted(Path(raw_dir).glob("*")):
        if not src.is_file():
            continue
        try:
            outputs.append(parse_and_save(src))
        except (ValueError, NotImplementedError) as exc:
            print(f"skip {src.name}: {exc}")
    return outputs


if __name__ == "__main__":
    import sys

    targets = [Path(a) for a in sys.argv[1:]]
    if not targets:
        targets = [p for p in sorted(RAW_DIR.glob("*")) if p.is_file()]
    if not targets:
        raise SystemExit(f"No raw scan files. Drop scanner output into {RAW_DIR}/")

    for src in targets:
        try:
            doc = parse_file(src)
            out = parse_and_save(src)
            print(
                f"{src.name}: {doc['scan']['detected_tool']} -> {out.name} "
                f"({len(doc['findings'])} findings, {len(doc['hosts'])} hosts)"
            )
        except (ValueError, NotImplementedError) as exc:
            print(f"{src.name}: {exc}")
