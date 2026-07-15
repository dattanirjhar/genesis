"""
Connector registry — the catalogue of available tools.

Loads each connector module and exposes its Tool by id. Adding a tool means
adding a connector module and one entry here; the planner and executor never
change.
"""

from __future__ import annotations

import importlib

from automation.execution.connectors.base import Tool

# Connector modules under automation/execution/connectors/.
# Registry order is phase order: for tools that become runnable in the same
# dependency round, the planner emits them in this order — so the plan reads
# recon -> fingerprint -> discovery -> network -> vuln -> validation.
_CONNECTOR_MODULES = [
    # reconnaissance
    "subfinder",
    "amass",
    "httpx",
    # fingerprinting
    "whatweb",
    # discovery (katana first — real links; gobuster enriches by brute force)
    "katana",
    "gobuster",
    # network (only after a host resolves): naabu finds ports, nmap detects services
    "naabu",
    "nmap",
    # vulnerability discovery
    "nuclei",
    "nikto",
    # validation (approval required)
    "sqlmap",
]


def all_tools() -> dict[str, Tool]:
    """Return every registered tool, keyed by id."""
    tools: dict[str, Tool] = {}
    for name in _CONNECTOR_MODULES:
        module = importlib.import_module(f"automation.execution.connectors.{name}")
        tools[module.TOOL.id] = module.TOOL
    return tools


def get(tool_id: str) -> Tool:
    return all_tools()[tool_id]


def producers() -> dict[str, list[str]]:
    """Map each produced signal type to the tool ids that produce it."""
    from automation.execution.signals import signal_type

    result: dict[str, list[str]] = {}
    for tool in all_tools().values():
        for produced in tool.produces:
            result.setdefault(signal_type(produced), []).append(tool.id)
    return result
