"""Connector: httpx (ProjectDiscovery) — probe which hosts serve live web."""

from __future__ import annotations

from automation.execution import signals as S
from automation.execution.connectors.base import Tool
from config import RAW_DIR


def _cmd(target: str) -> list[str]:
    out = RAW_DIR / "scan_httpx.jsonl"
    return ["httpx", "-u", target, "-json", "-o", str(out)]


TOOL = Tool(
    id="httpx",
    category="recon",
    phase="reconnaissance",
    risk="safe",
    passive=True,
    consumes=(S.ASSET_SUBDOMAIN,),
    produces=(S.WEB_ENDPOINT, S.ASSET_HOST),
    outputs=("scan_httpx.jsonl",),
    description="Resolve subdomains to live HTTP(S) endpoints (and their hosts).",
    build_command=_cmd,
)
