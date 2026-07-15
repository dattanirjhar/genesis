"""Connector: naabu — fast port discovery, so nmap only version-scans open ports."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_naabu.jsonl"
    return ["naabu", "-host", target, "-json", "-o", str(out)]


TOOL = Tool(
    id="naabu",
    category="network",
    phase="network",
    risk="enumeration",
    passive=False,
    cost="low",
    timeout=300,
    tags=("network", "port-discovery"),
    consumes=(S.ASSET_HOST,),
    produces=(S.NETWORK_PORT,),
    outputs=("scan_naabu.jsonl",),
    description="Rapidly find open ports so nmap can target its service scan.",
    build_command=_cmd,
)
