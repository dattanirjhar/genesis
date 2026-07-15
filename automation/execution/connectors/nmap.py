"""Connector: nmap — service/version + vuln script scan."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_nmap.xml"
    return ["nmap", "-sV", "--script", "vulners", "-oX", str(out), target]


TOOL = Tool(
    id="nmap",
    category="network",
    phase="network",
    risk="enumeration",
    passive=False,
    cost="medium",
    timeout=900,
    tags=("network", "service-detection"),
    consumes=(S.NETWORK_PORT,),
    produces=(S.NETWORK_SERVICE,),
    outputs=("scan_nmap.xml",),
    description="Service/version detection on open ports; flag known CVEs.",
    build_command=_cmd,
)
