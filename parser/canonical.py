"""
Canonical schema — the internal contract every parser produces and every
downstream stage consumes.

This module owns the schema and its builders. It depends on nothing else in the
project, so tool parsers can import it without pulling in the dispatcher.

Canonical JSON document shape:

    {
      "scan":    {"tool", "scanner", "args", "started", "raw_file", "detected_tool"},
      "hosts":   [{"host", "hostnames", "state"}, ...],
      "findings": [<finding>, ...]
    }

Each <finding> carries exactly CANONICAL_FIELDS, so knowledge_builder can hand
one finding at a time to the LLM without any format knowledge. These names are
the contract consumed by llm/prompts/knowledge.md.
"""

from __future__ import annotations

from pathlib import Path

CANONICAL_FIELDS = (
    "finding_id",
    "host",
    "port",
    "protocol",
    "service",
    "scanner",
    "tool",
    "severity",
    "cve",
    "name",
    "description",
    "evidence",
    "banner",
    "product",
    "version",
    "state",
    "validated",
    "timestamp",
)


def finding_id(tool: str, *parts) -> str:
    """Build a deterministic finding id: same scan input -> same id, always.

    Determinism matters: this id becomes a knowledge filename and a vector-DB
    key, so it must never depend on time or randomness.
    """
    slug = "-".join(str(p) for p in parts if p not in (None, ""))
    return f"{tool}-{slug}" if slug else tool


def make_finding(**fields) -> dict:
    """Return a finding dict with all CANONICAL_FIELDS present.

    Callers pass whatever they extracted; everything else gets a safe default.
    A finding must at least have finding_id, scanner, and tool. Unknown fields
    are rejected so a parser can't silently invent a field off-contract.
    """
    for required in ("finding_id", "scanner", "tool"):
        if not fields.get(required):
            raise ValueError(f"finding is missing required field: {required}")

    finding = {
        "finding_id": None,
        "host": "unknown",
        "port": None,
        "protocol": "",
        "service": "unknown",
        "scanner": None,
        "tool": None,
        "severity": "informational",
        "cve": "none",
        "name": "",
        "description": "",
        "evidence": "",
        "banner": "",
        "product": "",
        "version": "",
        "state": "",
        "validated": False,
        "timestamp": "unknown",
    }
    unknown = set(fields) - set(CANONICAL_FIELDS)
    if unknown:
        raise ValueError(f"finding has unknown fields: {sorted(unknown)}")
    finding.update(fields)
    return finding


def canonical_document(
    tool: str,
    findings: list[dict],
    hosts: list[dict] | None = None,
    args: str = "",
    started: str = "unknown",
    raw_file: str | Path = "",
) -> dict:
    """Assemble the top-level Canonical JSON document."""
    return {
        "scan": {
            "tool": tool,
            "scanner": tool,
            "args": args,
            "started": started,
            "raw_file": str(raw_file),
        },
        "hosts": hosts or [],
        "findings": findings,
    }
