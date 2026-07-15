"""Connector: subfinder — fast passive subdomain discovery."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_subfinder.txt"
    return ["subfinder", "-d", target, "-silent", "-o", str(out)]


TOOL = Tool(
    id="subfinder",
    category="recon",
    phase="reconnaissance",
    risk="safe",
    passive=True,
    consumes=(S.ASSET_DOMAIN,),
    produces=(S.ASSET_SUBDOMAIN,),
    outputs=("scan_subfinder.txt",),
    description="Passive subdomain enumeration from public sources.",
    build_command=_cmd,
)
