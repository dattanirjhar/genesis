"""Connector: whatweb — fingerprint web technologies (produces the branch signal)."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_whatweb.json"
    return ["whatweb", "--log-json", str(out), target]


TOOL = Tool(
    id="whatweb",
    category="web",
    phase="fingerprinting",
    risk="safe",
    passive=True,
    consumes=(S.WEB_ENDPOINT,),
    produces=(S.TECHNOLOGY,),
    outputs=("scan_whatweb.json",),
    description="Fingerprint web server, CMS, and frameworks (e.g. WordPress, nginx).",
    build_command=_cmd,
)
