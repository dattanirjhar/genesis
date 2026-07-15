"""
Genesis developer console — dispatch only.

An interactive REPL over the whole pipeline. Every command lives in its own
module under tools/commands/; this file only wires them into a registry and
routes a typed line to the right handler. Adding a command means adding a module
with a COMMANDS dict — nothing here changes except the import list.

    Genesis> help

Ingest:   ingest   (data/raw -> parser -> knowledge -> embedding; no scanners)
Stages:   parser  knowledge  chunk  embed  index
Inspect:  show  stats  list  inspect <id>  inspect-json [stem]
          inspect-chunk <id>  inspect-vector <id>
Query:    search <text>        reason <question>
Output:   report [md|docx]
Manage:   clean  quit

Run:
    python -m tools.genesis            # start the console
    python -m tools.genesis show       # run one command and exit
    python -m tools.genesis ingest     # ingest data/raw and exit
    python tools/genesis.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.client import is_available  # noqa: E402
from tools.commands import (  # noqa: E402
    chunk,
    clean,
    doctor,
    embed,
    index,
    ingest,
    inspect,
    knowledge,
    parser,
    reason,
    report,
    run,
    scan,
    search,
    show,
    stats,
    status,
)

# Merge every command module's COMMANDS into one registry. genesis stays pure
# dispatch; each module owns its command(s).
_MODULES = [
    doctor, run, scan, parser, knowledge, chunk, embed, index, ingest,
    status, show, stats, inspect, search, reason, report, clean,
]
REGISTRY: dict = {}
for _module in _MODULES:
    REGISTRY.update(_module.COMMANDS)

HELP = """Commands  (workflow: run <target> -> reason -> report)
  Preflight: doctor
  One-shot:  run <target> [--deep] [--yes]   (scan -> ingest -> status)
  Scan:      scan <target> [--deep] [--yes] [--plan]
  Ingest:    ingest   (data/raw -> parser -> knowledge -> embedding)
  Stages:    parser  knowledge  chunk  embed  index
  Inspect:   status  show  stats  list  inspect <id>  inspect-json [stem]
             inspect-chunk <id>  inspect-vector <id>
  Query:     search <text>       reason <question>
  Output:    report [md|docx]
  Manage:    clean  help  quit"""


def dispatch(line: str) -> bool:
    """Run one command line. Returns False to exit the REPL."""
    line = line.strip()
    if not line:
        return True
    cmd, _, arg = line.partition(" ")
    cmd = cmd.lower()
    if cmd in {"quit", "exit", "q"}:
        return False
    if cmd in {"help", "?"}:
        print(HELP)
        return True
    handler = REGISTRY.get(cmd)
    if not handler:
        print(f"Unknown command: {cmd}  (try `help`)")
        return True
    try:
        handler(arg.strip())
    except Exception as exc:  # noqa: BLE001 - keep the console alive
        print(f"Error: {exc}")
    return True


def main() -> int:
    if not is_available():
        print("WARNING: Ollama not reachable — `knowledge` and `reason` will fail.\n")

    # One-shot mode: `python -m tools.genesis show`
    if len(sys.argv) > 1:
        dispatch(" ".join(sys.argv[1:]))
        return 0

    print("Genesis developer console. Type `help`, or `quit` to exit.")
    while True:
        try:
            line = input("\nGenesis> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not dispatch(line):
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
