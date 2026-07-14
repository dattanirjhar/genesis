"""Command: rebuild — parser -> knowledge -> index, without stopping."""

from __future__ import annotations

import time

from tools.commands import index as index_cmd
from tools.commands import knowledge as knowledge_cmd
from tools.commands import parser as parser_cmd


def run(_: str = "") -> None:
    print("Rebuilding: parser -> knowledge -> index (chunk + embed inside index)")
    start = time.perf_counter()
    parser_cmd.run()
    knowledge_cmd.run()
    index_cmd.run()
    print(f"\nTotal rebuild time: {time.perf_counter() - start:.2f} sec")


COMMANDS = {"rebuild": run}
