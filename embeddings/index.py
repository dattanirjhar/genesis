"""
Index — persist and query chunk vectors in local Qdrant.

Pipeline position:

    chunk + vector  ->  Index  ->  Qdrant  (and: vector -> Index -> nearest chunks)

Responsibility: the store. This is the ONLY module that knows QdrantClient
exists. Qdrant runs in embedded mode (a path on disk, no server, no Docker), so
the same code moves to a hosted Qdrant later by changing only the client
constructor — everything else is identical.
"""

from __future__ import annotations

import uuid
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import COLLECTION_NAME, QDRANT_PATH, TOP_K
from embeddings import embed

# Fixed namespace so a chunk id always maps to the same Qdrant point id.
# (Qdrant point ids must be int or UUID; our chunk ids are strings.)
_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "genesis.pentest.local")


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    """Open the embedded Qdrant database once and reuse it (holds a file lock)."""
    return QdrantClient(path=str(QDRANT_PATH))


def _point_id(chunk_id: str) -> str:
    """Deterministically map a string chunk id to a valid Qdrant UUID point id."""
    return str(uuid.uuid5(_ID_NAMESPACE, chunk_id))


def ensure_collection(dim: int) -> None:
    """Create the collection on first use; open the existing one afterwards.

    The vector size is passed in (derived from the model) rather than hardcoded,
    so swapping EMBED_MODEL cannot silently create a mis-sized collection.
    """
    client = get_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )


def index_chunks(chunks: list[dict]) -> int:
    """Embed and upsert chunks into Qdrant. Returns the number indexed.

    Re-indexing the same finding overwrites its point (deterministic id), so the
    index stays a clean mirror of the Markdown knowledge base.
    """
    if not chunks:
        return 0

    vectors = embed.embed_texts([chunk["text"] for chunk in chunks])
    ensure_collection(len(vectors[0]))

    points = []
    for chunk, vector in zip(chunks, vectors):
        payload = dict(chunk["metadata"])
        payload["chunk_id"] = chunk["id"]
        payload["text"] = chunk["text"]
        points.append(
            PointStruct(id=_point_id(chunk["id"]), vector=vector, payload=payload)
        )

    get_client().upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_points(vector: list[float], top_k: int = TOP_K) -> list[dict]:
    """Return the payloads of the top_k nearest points to a query vector.

    Each result is the stored payload plus a "score". Returns [] if nothing has
    been indexed yet.
    """
    client = get_client()
    if not client.collection_exists(COLLECTION_NAME):
        return []

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=vector,
        limit=top_k,
        with_payload=True,
    )
    results = []
    for point in response.points:
        payload = dict(point.payload or {})
        payload["score"] = point.score
        results.append(payload)
    return results


if __name__ == "__main__":
    # Build the index from the current Markdown knowledge base.
    from embeddings import chunker

    chunks = chunker.chunk_directory()
    if not chunks:
        raise SystemExit(f"No knowledge to index in {chunker.FINDINGS_DIR}/")
    count = index_chunks(chunks)
    print(f"Indexed {count} chunk(s) into '{COLLECTION_NAME}' at {QDRANT_PATH}")
