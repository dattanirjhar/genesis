"""Connector: nikto — web server scanner. Branches on technology=nginx."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_nikto.json"
    return ["nikto", "-h", target, "-Format", "json", "-output", str(out)]


TOOL = Tool(
    id="nikto",
    category="web",
    phase="vuln-discovery",
    risk="enumeration",
    passive=False,
    consumes=(S.WEB_ENDPOINT,),
    when=(f"{S.TECHNOLOGY}=nginx",),
    produces=(S.VULNERABILITY,),
    outputs=("scan_nikto.json",),
    description="Scan a web server for dangerous files and misconfigurations.",
    build_command=_cmd,
)
