"""Connector: amass — passive subdomain / attack-surface enumeration."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_amass.jsonl"
    return ["amass", "enum", "-passive", "-d", target, "-json", str(out)]


TOOL = Tool(
    id="amass",
    category="recon",
    phase="reconnaissance",
    risk="safe",
    passive=True,
    consumes=(S.ASSET_DOMAIN,),
    produces=(S.ASSET_SUBDOMAIN,),
    outputs=("scan_amass.jsonl",),
    description="Enrich attack surface with passive DNS enumeration.",
    build_command=_cmd,
)
