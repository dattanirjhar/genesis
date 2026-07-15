"""
Tool connector abstraction.

A connector is pure metadata plus a command builder. It knows how to turn a
target into an argv and which raw artifacts it produces — nothing else. It does
NOT know about RAG, Markdown, Qdrant, or reports. The execution layer's whole
job is: target -> run tool -> raw artifact in data/raw/. Genesis starts there.

The metadata is a typed capability contract: `consumes` and `produces` are
signals from automation.execution.signals, and `when` adds value-level
conditions ("technology=wordpress"). The planner derives a valid execution graph
from these — there is no hand-written workflow. To swap subprocess execution for
an MCP call later, only executor.py changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Tool:
    id: str                              # CLI/binary name, also the registry key
    category: str                        # recon | network | web | exploitation
    phase: str                           # reconnaissance | enumeration | vuln-scan | exploitation
    build_command: Callable[[str], list[str]]  # target -> argv

    risk: str = "safe"                   # safe | enumeration | intrusive
    approval_required: bool = False      # gate before running (intrusive tools)
    passive: bool = True                 # does it touch the target actively?
    optional: bool = False               # enrichment tool — only with --deep

    # Typed capability contract — the planner reasons from these.
    consumes: tuple[str, ...] = ()       # signal TYPES required (all present)
    produces: tuple[str, ...] = ()       # signal types yielded
    when: tuple[str, ...] = ()           # value conditions "type=value" (all met)

    # Planner hints (unused by the core loop today; available for future policy
    # like quick/deep modes or choosing between producers of the same capability).
    cost: str = "medium"                 # low | medium | high
    timeout: int = 300                   # seconds; enforced by the executor
    produces_confidence: float = 1.0     # how reliable its signals are (0..1)
    tags: tuple[str, ...] = ()           # free-form labels, e.g. ("web","fingerprint")

    outputs: tuple[str, ...] = ()        # raw artifact names written to data/raw/
    description: str = ""

    def command(self, target: str) -> list[str]:
        """Build the argv to run this tool against a target."""
        return self.build_command(target)

    def is_installed(self) -> bool:
        """Whether the tool's correct binary can be resolved."""
        from automation.execution.tools import is_available
        return is_available(self.id)
