"""
WhatWeb parser — WhatWeb --log-json output into Canonical JSON.

WhatWeb writes a JSON array (or object) of targets, each with a `plugins` map of
detected technologies:

    {"target": "http://site/", "http_status": 200,
     "plugins": {"nginx": {"version": ["1.19.0"]}, "PHP": {"version": ["5.6.40"]},
                 "HTTPServer": {"string": ["nginx/1.19.0"]}, "Title": {...}}}

One finding per target summarizing its technology stack (informational — this is
attack-surface fingerprinting, not a vulnerability).
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

from parser.canonical import canonical_document, finding_id, make_finding

# Non-technology WhatWeb plugins to skip when listing the stack.
_SKIP = {"Title", "Country", "IP", "HTTPServer", "Script", "UncommonHeaders",
         "RedirectLocation", "Meta-Author", "Cookies", "HttpOnly"}


def matches(sample: str) -> bool:
    """WhatWeb JSON pairs a target with a plugins map."""
    return '"plugins"' in sample and '"target"' in sample


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
            line = line.strip().rstrip(",")
            if line in ("", "[", "]"):
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records


def _tech_list(plugins: dict) -> list[str]:
    techs = []
    for name, meta in plugins.items():
        if name in _SKIP:
            continue
        versions = (meta or {}).get("version") or []
        techs.append(f"{name} {', '.join(versions)}".strip() if versions else name)
    return techs


def parse(path):
    records = _load(open(path, encoding="utf-8", errors="ignore").read())

    findings: list[dict] = []
    hosts: list[dict] = []

    for rec in records:
        target = rec.get("target") or "unknown"
        host = urlparse(target).hostname or target
        scheme = urlparse(target).scheme or "http"
        plugins = rec.get("plugins") or {}
        techs = _tech_list(plugins)
        server = ((plugins.get("HTTPServer") or {}).get("string") or [""])[0]
        title = ((plugins.get("Title") or {}).get("string") or [""])[0]

        tech_str = ", ".join(techs) if techs else "no notable technologies"
        description = f"WhatWeb fingerprinted {target}: {tech_str}."
        if server:
            description += f" Server: {server}."

        findings.append(
            make_finding(
                finding_id=finding_id("whatweb", host),
                host=host,
                service=scheme,
                scanner="whatweb",
                tool="whatweb",
                severity="informational",
                name=f"Web technologies at {host}",
                description=description,
                evidence=f"{target} [{rec.get('http_status', '?')}] {tech_str}"
                         + (f" | title: {title}" if title else ""),
                banner=server or tech_str,
            )
        )
        hosts.append({"host": host, "hostnames": [host], "state": "up"})

    return canonical_document("whatweb", findings, hosts=hosts, raw_file=path)
