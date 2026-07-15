"""
httpx parser — ProjectDiscovery httpx JSONL into Canonical JSON.

httpx probes hosts and emits one JSON object per live endpoint with fields like
url, host, port, scheme, status_code, title, webserver, and tech. Each live
endpoint becomes an informational finding recording the exposed web service.
"""

from __future__ import annotations

import json
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding


def matches(sample: str) -> bool:
    """httpx records carry a url plus a status_code / scheme."""
    return '"url"' in sample and ('"status_code"' in sample or '"scheme"' in sample)


def _load(text: str) -> list[dict]:
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
                continue
        return records


def parse(path: str | Path) -> dict:
    findings: list[dict] = []
    seen_hosts: dict[str, dict] = {}

    for rec in _load(Path(path).read_text(encoding="utf-8", errors="ignore")):
        url = rec.get("url") or rec.get("input") or "unknown"
        host = rec.get("host") or rec.get("input") or url
        scheme = rec.get("scheme") or "http"

        raw_port = rec.get("port")
        try:
            port = int(raw_port) if raw_port not in (None, "") else None
        except (TypeError, ValueError):
            port = None

        status = rec.get("status_code")
        title = rec.get("title") or ""
        webserver = rec.get("webserver") or ""
        tech = rec.get("tech") or rec.get("technologies") or []
        if isinstance(tech, str):
            tech = [tech]
        tech_str = ", ".join(tech)
        banner = " / ".join(x for x in (webserver, tech_str) if x)

        detail = ", ".join(
            b for b in (
                f"HTTP {status}" if status is not None else "",
                f"title '{title}'" if title else "",
                f"server {webserver}" if webserver else "",
                f"tech {tech_str}" if tech_str else "",
            ) if b
        )
        description = f"Live web service at {url} ({detail})." if detail else \
            f"Live web service at {url}."

        findings.append(
            make_finding(
                finding_id=finding_id("httpx", host, port),
                host=host,
                port=port,
                protocol="tcp",
                service=scheme,
                scanner="httpx",
                tool="httpx",
                severity="informational",
                name=f"Live web service {url}",
                description=description,
                evidence=f"{url} [{status}] {banner}".strip(),
                banner=banner,
                product=webserver,
            )
        )
        seen_hosts.setdefault(host, {"host": host, "hostnames": [], "state": "up"})

    return canonical_document(
        "httpx", findings, hosts=list(seen_hosts.values()), raw_file=path
    )
