"""Connector: sqlmap — SQL injection validation (intrusive, needs parameters)."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_sqlmap"
    return ["sqlmap", "-u", target, "--batch", "--output-dir", str(out)]


TOOL = Tool(
    id="sqlmap",
    category="exploitation",
    phase="validation",
    risk="intrusive",
    approval_required=True,
    passive=False,
    cost="high",
    timeout=1800,
    tags=("web", "injection"),
    consumes=(S.WEB_PARAMETER,),
    produces=(S.VULNERABILITY,),
    outputs=("scan_sqlmap/",),
    description="Probe discovered parameters for SQL injection. Run last, with approval.",
    build_command=_cmd,
)
