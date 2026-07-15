"""
Katana parser — Katana JSONL crawl output into Canonical JSON.

Katana (-jsonl) emits one JSON object per crawled URL, typically nested:

    {"timestamp": "...", "request": {"method": "GET", "endpoint": "http://site/x.php"},
     "response": {"status_code": 200}}

It may also emit a flat {"endpoint": "..."} or a plain URL per line. All are
handled. Because a crawl can surface many URLs, endpoints are aggregated into ONE
attack-surface finding per host (a site map) rather than one finding per URL —
keeping knowledge-building cost bounded.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

from parser.canonical import canonical_document, finding_id, make_finding


def matches(sample: str) -> bool:
    """Katana JSONL carries an endpoint alongside request/response objects."""
    return '"endpoint"' in sample and ('"request"' in sample or '"response"' in sample)


def _endpoint(rec: dict) -> str | None:
    req = rec.get("request") or {}
    return rec.get("endpoint") or req.get("endpoint") or rec.get("url")


def parse(path):
    text = open(path, encoding="utf-8", errors="ignore").read()

    by_host: dict[str, list[str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            # plain URL line
            rec = {"endpoint": line} if line.startswith("http") else {}
        url = _endpoint(rec)
        if not url:
            continue
        host = urlparse(url).hostname or "unknown"
        by_host.setdefault(host, [])
        if url not in by_host[host]:
            by_host[host].append(url)

    findings: list[dict] = []
    hosts: list[dict] = []
    for host, urls in by_host.items():
        listing = "\n".join(f"- {u}" for u in urls[:50])
        more = f" (+{len(urls) - 50} more)" if len(urls) > 50 else ""
        findings.append(
            make_finding(
                finding_id=finding_id("katana", host),
                host=host,
                service="http",
                scanner="katana",
                tool="katana",
                severity="informational",
                name=f"Discovered {len(urls)} endpoint(s) on {host}",
                description=f"Katana crawled {len(urls)} endpoint(s) on {host}{more}.",
                evidence=listing,
            )
        )
        hosts.append({"host": host, "hostnames": [host], "state": "up"})

    return canonical_document("katana", findings, hosts=hosts, raw_file=path)
