"""
Command: run — one-shot scan -> ingest -> status.

    Genesis> run http://testphp.vulnweb.com [--deep] [--yes]

The smooth default path: it scans the target into data/raw, ingests everything
into knowledge + vectors, and prints status. After it finishes, just ask:

    Genesis> reason
    Genesis> report

The individual stages (scan, ingest, status) remain available for fine control.
"""

from __future__ import annotations

from tools.commands import ingest as ingest_cmd
from tools.commands import scan as scan_cmd
from tools.commands import status as status_cmd


def run(arg: str = "") -> None:
    if not arg.split():
        print("  usage: run <target> [--deep] [--yes]")
        return

    print("== scan ==")
    scan_cmd.run(arg)
    print("\n== ingest ==")
    ingest_cmd.run()
    print("\n== status ==")
    status_cmd.run()
    print("\nReady. Ask: `reason`   Draft: `report`")


COMMANDS = {"run": run}
