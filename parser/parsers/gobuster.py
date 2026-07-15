"""
gobuster parser — directory/content enumeration output into Canonical JSON.

gobuster prints one discovered path per line, e.g.

    /admin                (Status: 200) [Size: 1234]

Each becomes an informational content-discovery finding. gobuster's output does
not record the target host per line, so host is left unknown — the path is the
evidence.
"""

from __future__ import annotations

import re
from pathlib import Path

from parser.canonical import canonical_document, finding_id, make_finding

_LINE = re.compile(
    r"^(?P<path>/\S*)\s+\(Status:\s*(?P<status>\d+)\)"
    r"(?:\s*\[Size:\s*(?P<size>\d+)\])?"
)


def matches(sample: str) -> bool:
    """gobuster result lines contain a (Status: NNN) marker."""
    return "(Status:" in sample


def parse(path: str | Path) -> dict:
    findings: list[dict] = []

    for raw in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        match = _LINE.match(raw.strip())
        if not match:
            continue

        found = match["path"]
        status = match["status"]
        size = match.group("size")
        evidence = f"{found} (Status: {status})" + (f" [Size: {size}]" if size else "")
        description = (
            f"Content discovery: {found} returned HTTP {status}"
            + (f", size {size} bytes" if size else "")
            + "."
        )

        findings.append(
            make_finding(
                finding_id=finding_id("gobuster", found, status),
                host="unknown",
                protocol="tcp",
                service="http",
                scanner="gobuster",
                tool="gobuster",
                severity="informational",
                name=f"Discovered path {found} (HTTP {status})",
                description=description,
                evidence=evidence,
            )
        )

    return canonical_document("gobuster", findings, raw_file=path)
