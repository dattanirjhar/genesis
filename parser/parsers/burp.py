"""
Burp Suite parser — STUB.

Detection is implemented so the dispatcher routes Burp files here; parsing is
not yet implemented. Drop a real Burp XML export into data/raw/ and implement
parse() following the contract below.

Burp exports issues as XML with an <issues> root:

    <issues burpVersion="...">
      <issue>
        <name>...</name> <host>...</host> <path>...</path>
        <severity>High|Medium|Low|Information</severity>
        <confidence>Certain|Firm|Tentative</confidence>
        <issueDetail>...</issueDetail> <vulnerabilityClassifications>...</vulnerabilityClassifications>
      </issue>
    </issues>

Map each <issue> to a finding via make_finding(): severity -> severity,
host -> host, name -> name, issueDetail -> description/evidence, any CVE in the
classifications -> cve. Return canonical_document("burp", findings, ...).
"""

from __future__ import annotations

from pathlib import Path


def matches(sample: str) -> bool:
    """Burp XML exports open with an <issues> root element."""
    return "<issues" in sample and "burp" in sample.lower()


def parse(path: str | Path) -> dict:
    raise NotImplementedError(
        "Burp parser not yet implemented. Detection and the Canonical JSON "
        "contract are in place; implement parse() when you have a sample export."
    )
