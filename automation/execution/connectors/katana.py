"""Connector: katana — crawl a live web host for endpoints and parameters."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_katana.jsonl"
    return ["katana", "-u", target, "-jsonl", "-o", str(out)]


TOOL = Tool(
    id="katana",
    category="web",
    phase="discovery",
    risk="enumeration",
    passive=False,
    cost="medium",
    timeout=600,
    tags=("web", "crawl"),
    consumes=(S.WEB_ENDPOINT,),
    produces=(S.WEB_ENDPOINT, S.WEB_PARAMETER),
    outputs=("scan_katana.jsonl",),
    description="Crawl a live web host to discover endpoints and injectable parameters.",
    build_command=_cmd,
)
