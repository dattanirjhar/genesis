"""
OpenVAS / GVM parser — STUB.

Detection is implemented so the dispatcher routes OpenVAS files here; parsing is
not yet implemented. Drop a real GVM/OpenVAS XML report into data/raw/ and
implement parse() following the contract below.

OpenVAS (Greenbone) XML reports use a <report> root and carry <result> elements:

    <report>
      <results>
        <result>
          <host>...</host> <port>443/tcp</port>
          <nvt oid="..."><name>...</name>
            <cve>CVE-...</cve>
            <severities><severity><value>7.5</value></severity></severities>
          </nvt>
          <threat>High|Medium|Low|Log</threat>
          <description>...</description>
        </result>
      </results>
    </report>

Map each <result> to a finding via make_finding(): threat -> severity,
host -> host, port -> port/service, nvt/name -> name, cve -> cve,
description -> description/evidence. Return canonical_document("openvas", ...).
"""

from __future__ import annotations

from pathlib import Path


def matches(sample: str) -> bool:
    """GVM/OpenVAS reports mention openvas/greenbone or use GVM report elements."""
    low = sample.lower()
    return (
        "openvas" in low
        or "greenbone" in low
        or "<get_reports_response" in low
        or ("<report" in low and "<nvt" in low)
    )


def parse(path: str | Path) -> dict:
    raise NotImplementedError(
        "OpenVAS parser not yet implemented. Detection and the Canonical JSON "
        "contract are in place; implement parse() when you have a sample report."
    )
