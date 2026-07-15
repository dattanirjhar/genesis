"""
sqlmap parser — STUB.

Detection is implemented so the dispatcher routes sqlmap output here; parsing is
not yet implemented. sqlmap writes a directory of logs plus a session database
rather than a single clean artifact, so real parsing needs a sample to build
against. Point parse() at the target log or the CSV results file when available.

A confirmed injection appears in the log as, e.g.:

    sqlmap identified the following injection point(s):
    Parameter: id (GET)
        Type: boolean-based blind
        Payload: id=1 AND 1=1

Map each injection point to a finding via make_finding(): severity high,
validated True (sqlmap confirms exploitability), the parameter/type as name, the
payload as evidence. Return canonical_document("sqlmap", findings, ...).
"""

from __future__ import annotations

from pathlib import Path


def matches(sample: str) -> bool:
    """sqlmap logs mention sqlmap, or an injection point (Parameter/Payload)."""
    low = sample.lower()
    return "sqlmap" in low or ("parameter:" in low and "payload:" in low)


def parse(path: str | Path) -> dict:
    raise NotImplementedError(
        "sqlmap parser not yet implemented. Detection and the Canonical JSON "
        "contract are in place; implement parse() when you have a sample log."
    )
