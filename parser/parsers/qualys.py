"""
Qualys parser — STUB.

Detection is implemented so the dispatcher routes Qualys files here; parsing is
not yet implemented. Drop a real Qualys XML report into data/raw/ and implement
parse() following the contract below.

Qualys reports come in a few XML shapes (VM scan, WAS scan, asset data report).
A common VM shape nests detections under hosts:

    <ASSET_DATA_REPORT>
      <HOST_LIST>
        <HOST>
          <IP>...</IP> <DNS>...</DNS>
          <VULN_INFO_LIST>
            <VULN_INFO>
              <QID>...</QID> <SEVERITY>1-5</SEVERITY>
              <CVE_ID_LIST><CVE_ID><ID>CVE-...</ID></CVE_ID></CVE_ID_LIST>
              <RESULT>...</RESULT>
            </VULN_INFO>
          </VULN_INFO_LIST>
        </HOST>
      </HOST_LIST>
    </ASSET_DATA_REPORT>

Map each detection to a finding via make_finding(): Qualys SEVERITY 1-5 ->
severity band, IP -> host, QID/title -> name, CVE_ID -> cve, RESULT ->
evidence. Return canonical_document("qualys", findings, ...).
"""

from __future__ import annotations

from pathlib import Path


def matches(sample: str) -> bool:
    """Qualys reports name qualys or use Qualys-specific report roots."""
    low = sample.lower()
    return (
        "qualys" in low
        or "<asset_data_report" in low
        or "<was_scan_report" in low
        or "<scan_report" in low
    )


def parse(path: str | Path) -> dict:
    raise NotImplementedError(
        "Qualys parser not yet implemented. Detection and the Canonical JSON "
        "contract are in place; implement parse() when you have a sample report."
    )
