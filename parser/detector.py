"""
Detector — decide which tool produced a raw scan file.

Detection is content-based: each tool parser exposes a matches(sample) function
that inspects the first bytes of the file. The detector asks each parser, in a
defined order, and returns the first that recognizes the file. It knows nothing
about parsing itself — only routing.
"""

from __future__ import annotations

import importlib
from pathlib import Path

# Tool modules tried in order. The first whose matches() returns True wins. More
# specific signatures should come before more generic ones. (In the enterprise
# build this list moves to config so scanners can be toggled without code edits.)
PARSER_ORDER = ["nmap", "nuclei", "amass", "netexec", "burp", "openvas", "qualys"]


def _read_sample(path: Path, size: int = 4096) -> str:
    """Read the first bytes of a file as text for tool detection."""
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return fh.read(size)


def detect_tool(path: str | Path):
    """Detect which tool produced a file. Returns (name, module).

    Raises ValueError if no registered parser recognizes the file.
    """
    path = Path(path)
    sample = _read_sample(path)
    for name in PARSER_ORDER:
        module = importlib.import_module(f"parser.parsers.{name}")
        if module.matches(sample):
            return name, module
    raise ValueError(f"No parser recognized {path}. Supported: {PARSER_ORDER}")
