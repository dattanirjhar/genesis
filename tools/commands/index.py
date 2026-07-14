"""Command: index — chunks -> embedded Qdrant (chunk + embed + upsert)."""

from __future__ import annotations

from config import COLLECTION_NAME
from embeddings import chunker, index
from tools.commands._common import timed


def run(_: str = "") -> None:
    with timed("Qdrant Index"):
        chunks = chunker.chunk_directory()
        if not chunks:
            print("  No chunks. Build knowledge first.")
            return
        indexed = index.index_chunks(chunks)
        points = index.get_client().get_collection(COLLECTION_NAME).points_count
        print(f"  indexed this run: {indexed}   points in collection: {points}")


COMMANDS = {"index": run}
