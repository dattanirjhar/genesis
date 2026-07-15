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

HELP = """
Genesis scans a target, turns the results into searchable knowledge, and lets
you ask questions about it in plain English and draft a report.

TYPICAL SESSION
  1. doctor                             check everything is installed & running
  2. run http://testphp.vulnweb.com     scan the target and load the results
  3. reason                             ask questions about what was found
  4. report                             write up the findings

MAIN COMMANDS
  doctor                 Health check: models, database, tools, wordlists.
                         Run this first — it tells you if anything is missing.

  run <target>           The one-shot button. Scans the target, processes the
                         results, and shows status. After it finishes, use
                         `reason` and `report`. <target> can be a URL
                         (http://site), a domain (site.com), or an IP.

  reason                 Ask a question about the findings (RAG Q&A). Type it
                         when prompted, e.g. "What are the critical findings?".
                         Grounded in the scan — it won't make things up.

  report                 Write the findings to a Markdown report.
                         `report docx` for a Word file.

  status                 Where you are: target, counts, last scan, is the AI up.

TARGET SCOPE (how much to scan)
  run <target>           Targeted: assess just this one app/host.  (fast, default)
  run <target> --recon   Full footprint: also finds subdomains of the target
                         (subfinder/amass/httpx) before scanning.  (thorough)

SCAN DEPTH (extra flags for run / scan)
  --deep                 Also run brute-force directory discovery (gobuster).
  --yes                  Also run intrusive scanners (nuclei, sqlmap). Only use
                         on targets you are authorized to test.
  --plan                 Show what WOULD run, without running anything.

STEP-BY-STEP (if you don't want the one-shot `run`)
  scan <target> [flags]  Just run the tools -> raw files in data/raw/.
  ingest                 Process data/raw -> knowledge -> searchable vectors.
  search <text>          See what the AI retrieves for a query (no answer).

INSPECT / DEBUG
  inspect                Show how data flowed through the pipeline (per tool).
  inspect <id>           Show one finding in full (see `list` for ids).
  list                   List all finding ids.
  show                   Pipeline build status (READY / STALE).
  stats                  Counts, models, disk usage.

MANAGE
  clean                  Wipe scan data (raw, knowledge, vectors) for a fresh
                         target. Asks for confirmation.
  help                   This screen.        quit                Exit.

Advanced stage commands (parser, knowledge, chunk, embed, index,
inspect-json/-chunk/-vector) exist for debugging individual stages.
"""


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
