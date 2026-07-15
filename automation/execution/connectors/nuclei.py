"""Connector: nuclei — template-based vulnerability scanning (intrusive)."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_nuclei.jsonl"
    return ["nuclei", "-u", target, "-jsonl", "-o", str(out)]


TOOL = Tool(
    id="nuclei",
    category="web",
    phase="vuln-discovery",
    risk="intrusive",
    approval_required=True,
    passive=False,
    cost="high",
    timeout=1800,
    tags=("web", "vuln"),
    consumes=(S.WEB_ENDPOINT,),
    produces=(S.VULNERABILITY,),
    outputs=("scan_nuclei.jsonl",),
    description="Run community vulnerability templates against live endpoints.",
    build_command=_cmd,
)
