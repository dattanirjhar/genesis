"""
Nuclei parser — Nuclei JSON/JSONL into Canonical JSON.

Nuclei emits either newline-delimited JSON (`-jsonl`) or a JSON array
(`-json-export`). Both are handled. Each match becomes one finding, carrying the
template's severity and any CVE ids from its classification metadata.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding


def matches(sample: str) -> bool:
    """Nuclei records carry a template id and a matched-at location."""
    return (
        '"template-id"' in sample
        or '"templateID"' in sample
        or '"matched-at"' in sample
    )


def _load_records(text: str) -> list[dict]:
    """Load either a JSON array or newline-delimited JSON objects."""
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # tolerate stray non-JSON lines
        return records


def parse(path: str | Path) -> dict:
    records = _load_records(Path(path).read_text(encoding="utf-8"))

    findings: list[dict] = []
    seen_hosts: dict[str, dict] = {}

    for rec in records:
        info = rec.get("info") or {}
        template_id = rec.get("template-id") or rec.get("templateID") or "unknown"
        severity = (info.get("severity") or "unknown").lower()
        name = info.get("name") or template_id
        description = info.get("description") or ""

        host = rec.get("host") or rec.get("ip") or "unknown"
        raw_port = rec.get("port")
        try:
            port = int(raw_port) if raw_port not in (None, "") else None
        except (TypeError, ValueError):
            port = None

        # CVE ids live under info.classification.cve-id (list or string).
        classification = info.get("classification") or {}
        cve_ids = classification.get("cve-id") or classification.get("cve_id") or []
        if isinstance(cve_ids, str):
            cve_ids = [cve_ids]
        cve = ", ".join(sorted({c.upper() for c in cve_ids if c})) or "none"

        matched = rec.get("matched-at") or rec.get("matched") or host
        evidence = matched
        extracted = rec.get("extracted-results") or []
        if extracted:
            evidence += " | extracted: " + ", ".join(map(str, extracted))

        findings.append(
            make_finding(
                finding_id=finding_id("nuclei", template_id, host, port),
                host=host,
                port=port,
                protocol="tcp",
                service=rec.get("type") or "http",
                scanner="nuclei",
                tool="nuclei",
                severity=severity,
                cve=cve,
                name=name,
                description=description,
                evidence=evidence,
                timestamp=rec.get("timestamp") or "unknown",
            )
        )
        seen_hosts.setdefault(host, {"host": host, "hostnames": [], "state": "up"})

    return canonical_document(
        "nuclei", findings, hosts=list(seen_hosts.values()), raw_file=path
    )
