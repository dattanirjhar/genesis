"""Connector: gobuster — directory / content enumeration."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR, WORDLIST


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_gobuster.txt"
    return ["gobuster", "dir", "-u", target, "-w", str(WORDLIST), "-o", str(out)]


TOOL = Tool(
    id="gobuster",
    category="web",
    phase="discovery",
    risk="enumeration",
    passive=False,
    optional=True,          # enrichment only — katana finds real links first
    cost="high",
    timeout=600,
    tags=("web", "content-discovery"),
    consumes=(S.WEB_ENDPOINT,),
    produces=(S.WEB_DIRECTORY,),
    outputs=("scan_gobuster.txt",),
    description="Brute-force directories and files (enrichment; run with --deep).",
    build_command=_cmd,
)
