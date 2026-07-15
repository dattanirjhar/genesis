"""
Command: ingest — turn whatever is already in data/raw into searchable knowledge.

    data/raw  ->  parser  ->  knowledge  ->  embedding (Qdrant)

This does NOT run scanners. It ingests raw artifacts that are already on disk
(produced by `automation.run <target>` or by you running tools manually). That
decouples scanning from knowledge generation:

    automation.run target  ->  data/raw/  ->  Genesis> ingest  ->  ask / report

It is the parser + knowledge + index stages, timed as one operation.
"""

from __future__ import annotations

import time

from tools.commands import index as index_cmd
from tools.commands import knowledge as knowledge_cmd
from tools.commands import parser as parser_cmd


def run(_: str = "") -> None:
    print("Ingesting data/raw:  parser -> knowledge -> embedding")
    start = time.perf_counter()
    parser_cmd.run()
    knowledge_cmd.run()
    index_cmd.run()
    print(f"\nTotal ingest time: {time.perf_counter() - start:.2f} sec")
    print("Ready. Ask questions (`reason <q>`) or draft a report (`report`).")


COMMANDS = {"ingest": run}
