"""
Nikto parser — Nikto -Format json output into Canonical JSON.

Nikto emits a host object (or array of them) with a vulnerabilities list:

    {"host": "site", "ip": "1.2.3.4", "port": "80", "banner": "nginx/1.19.0",
     "vulnerabilities": [
        {"id": "999957", "method": "GET", "url": "/",
         "msg": "The anti-clickjacking X-Frame-Options header is not present."}]}

Each Nikto item becomes a finding (server misconfigurations / exposures), at low
severity by default; any CVE referenced in the item is captured.
"""

from __future__ import annotations

import json
import re

from parser.canonical import canonical_document, finding_id, make_finding

_CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.IGNORECASE)


def matches(sample: str) -> bool:
    """Nikto JSON contains a vulnerabilities list."""
    return '"vulnerabilities"' in sample


def _load(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else [data]


def parse(path):
    hosts_json = _load(open(path, encoding="utf-8", errors="ignore").read())

    findings: list[dict] = []
    hosts: list[dict] = []

    for block in hosts_json:
        host = block.get("host") or block.get("ip") or "unknown"
        port = block.get("port")
        try:
            port = int(port) if port not in (None, "") else None
        except (TypeError, ValueError):
            port = None
        banner = block.get("banner") or ""

        for item in block.get("vulnerabilities") or []:
            msg = item.get("msg") or item.get("message") or "Nikto finding"
            url = item.get("url") or "/"
            method = item.get("method") or "GET"
            refs = " ".join(str(item.get(k, "")) for k in ("references", "msg", "id"))
            cves = sorted({m.upper() for m in _CVE_RE.findall(refs)})

            findings.append(
                make_finding(
                    finding_id=finding_id("nikto", host, item.get("id") or url),
                    host=host,
                    port=port,
                    protocol="tcp",
                    service="http",
                    scanner="nikto",
                    tool="nikto",
                    severity="low",
                    cve=", ".join(cves) or "none",
                    name=msg[:80],
                    description=f"Nikto: {msg} (at {method} {url}).",
                    evidence=f"{method} {url} — {msg}",
                    banner=banner,
                )
            )
        hosts.append({"host": host, "hostnames": [], "state": "up"})

    return canonical_document("nikto", findings, hosts=hosts, raw_file=path)
