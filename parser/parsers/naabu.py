"""
naabu parser — naabu -json port-discovery output into Canonical JSON.

naabu emits one JSON object per open port:

    {"ip": "44.228.249.3", "port": 80, "protocol": "tcp", "host": "site"}

Each open port becomes an informational finding (exposed port), mirroring the
open-port findings nmap produces but from fast port discovery.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding


def matches(sample: str) -> bool:
    """naabu records carry an ip + port + protocol, and no web url/status."""
    return '"port"' in sample and '"protocol"' in sample and '"ip"' in sample \
        and '"url"' not in sample and '"status_code"' not in sample


def parse(path):
    findings: list[dict] = []
    hosts: dict[str, dict] = {}

    for raw in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue

        host = rec.get("host") or rec.get("ip") or "unknown"
        port = rec.get("port")
        proto = rec.get("protocol") or "tcp"
        try:
            port = int(port) if port not in (None, "") else None
        except (TypeError, ValueError):
            port = None

        findings.append(
            make_finding(
                finding_id=finding_id("naabu", host, proto, port),
                host=host,
                port=port,
                protocol=proto,
                service="unknown",
                scanner="naabu",
                tool="naabu",
                severity="informational",
                name=f"Open {proto}/{port} on {host}",
                description=f"naabu found {proto} port {port} open on {host}.",
                evidence=f"{host}:{port}/{proto}",
            )
        )
        hosts.setdefault(host, {"host": host, "hostnames": [], "state": "up"})

    return canonical_document("naabu", findings, hosts=list(hosts.values()),
                              raw_file=path)
