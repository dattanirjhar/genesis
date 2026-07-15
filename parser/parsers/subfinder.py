"""
subfinder parser — passive subdomain list into Canonical JSON.

subfinder writes one discovered hostname per line. Each becomes an
informational finding (attack surface), mirroring the amass parser.
"""

from __future__ import annotations

import re
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding

_DOMAIN = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9_-]{1,63}(?:\.[A-Za-z0-9_-]{1,63})+$"
)


def matches(sample: str) -> bool:
    """A bare list of hostnames — no JSON/XML, every line a domain."""
    if "{" in sample or "<" in sample:
        return False
    lines = [line.strip() for line in sample.splitlines() if line.strip()]
    if not lines:
        return False
    return all(_DOMAIN.match(line) for line in lines[:20])


def parse(path: str | Path) -> dict:
    findings: list[dict] = []
    hosts: list[dict] = []

    for raw in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        name = raw.strip()
        if not name or not _DOMAIN.match(name):
            continue
        findings.append(
            make_finding(
                finding_id=finding_id("subfinder", name),
                host=name,
                service="dns",
                scanner="subfinder",
                tool="subfinder",
                severity="informational",
                name=f"Discovered subdomain {name}",
                description=f"Subdomain {name} discovered via passive enumeration.",
                evidence=name,
            )
        )
        hosts.append({"host": name, "hostnames": [name], "state": "unknown"})

    return canonical_document("subfinder", findings, hosts=hosts, raw_file=path)
