"""Command: stats — detailed counts, collection config, models, disk usage."""

from __future__ import annotations

from pathlib import Path

from config import COLLECTION_NAME, EMBED_MODEL, MODEL_NAME, QDRANT_PATH
from embeddings import chunker, embed, index
from tools.commands._common import (
    FINDINGS_DIR,
    NORMALIZED_DIR,
    dir_size,
    fmt_bytes,
)


def run(_: str = "") -> None:
    print("\nGenesis stats\n-------------")
    print(f"  normalized JSON : {len(list(NORMALIZED_DIR.glob('*.json')))}")
    print(f"  knowledge files : {len(list(FINDINGS_DIR.glob('*.md')))}")
    print(f"  chunks          : {len(chunker.chunk_directory())}")

    client = index.get_client()
    if client.collection_exists(COLLECTION_NAME):
        info = client.get_collection(COLLECTION_NAME)
        try:
            vectors = info.config.params.vectors
            dim, distance = vectors.size, vectors.distance
        except AttributeError:
            dim, distance = embed.dimension(), "?"
        print(f"  collection      : {COLLECTION_NAME}")
        print(f"  points          : {info.points_count}")
        print(f"  dimension       : {dim}")
        print(f"  distance        : {distance}")
    else:
        print(f"  collection      : {COLLECTION_NAME} (not created yet)")

    print(f"  embedding model : {EMBED_MODEL}")
    print(f"  reasoning model : {MODEL_NAME}")
    print(f"  qdrant disk     : {fmt_bytes(dir_size(Path(QDRANT_PATH)))}")
    print(f"  knowledge disk  : {fmt_bytes(dir_size(FINDINGS_DIR))}")


COMMANDS = {"stats": run}
