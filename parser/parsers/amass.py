"""
Amass parser — Amass JSONL enumeration output into Canonical JSON.

Amass is an asset-discovery tool, so each discovered name becomes a finding: the
subdomain is the host, its resolved addresses are the evidence. Findings are
`informational` — they record attack surface, not a vulnerability.

Expected record shape (one JSON object per line):

    {"name": "sub.example.com", "domain": "example.com",
     "addresses": [{"ip": "1.2.3.4", "cidr": "...", "asn": 0, "desc": "..."}],
     "tag": "...", "sources": ["..."]}
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding


def matches(sample: str) -> bool:
    """Amass records pair a resolved name with an addresses array."""
    return '"addresses"' in sample and ('"domain"' in sample or '"tag"' in sample)


def _load_records(text: str) -> list[dict]:
    records = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def parse(path: str | Path) -> dict:
    records = _load_records(Path(path).read_text(encoding="utf-8"))

    findings: list[dict] = []
    hosts: list[dict] = []

    for rec in records:
        name = rec.get("name") or "unknown"
        addresses = rec.get("addresses") or []
        ips = [a.get("ip") for a in addresses if a.get("ip")]
        ip_str = ", ".join(ips) if ips else "no resolved address"

        sources = rec.get("sources") or []
        source_str = ", ".join(sources) if sources else ""
        description = f"Discovered host {name} resolving to {ip_str}."
        if source_str:
            description += f" Sources: {source_str}."

        findings.append(
            make_finding(
                finding_id=finding_id("amass", name),
                host=name,
                service="dns",
                scanner="amass",
                tool="amass",
                severity="informational",
                name=f"Discovered host {name}",
                description=description,
                evidence=ip_str,
                banner=ip_str,
            )
        )
        hosts.append({"host": name, "hostnames": [name], "state": "up"})

    return canonical_document("amass", findings, hosts=hosts, raw_file=path)
