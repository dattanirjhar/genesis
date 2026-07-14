"""Command: embed — chunks -> vectors (reports count/dimension, times the model)."""

from __future__ import annotations

from config import EMBED_MODEL
from embeddings import chunker, embed
from tools.commands._common import timed


def run(_: str = "") -> None:
    with timed("Embedding"):
        chunks = chunker.chunk_directory()
        if not chunks:
            print("  No chunks. Build knowledge first.")
            return
        vectors = embed.embed_texts([c["text"] for c in chunks])
        print(f"  model: {EMBED_MODEL}   dim: {embed.dimension()}")
        print(f"  vectors created: {len(vectors)}")


COMMANDS = {"embed": run}
