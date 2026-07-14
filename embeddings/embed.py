"""
Embed — chunk text into a vector, on CPU.

Pipeline position:

    chunk text  ->  Embed  ->  vector

Responsibility: text -> vector. Nothing else. No filesystem, no database.

The model (config.EMBED_MODEL = bge-small-en-v1.5) is loaded once and reused for
the life of the process — the same singleton discipline as the LLM client.
There is nothing to pull ahead of time: the first call downloads the model into
the Hugging Face cache, later runs reuse it.

bge is an asymmetric retrieval model: passages are embedded as-is, but queries
are prefixed with a short instruction, which measurably improves retrieval. So
this module exposes two entry points — embed_texts() for passages and
embed_query() for questions. Vectors are L2-normalized so Qdrant cosine
similarity behaves well.
"""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import EMBED_MODEL

# bge-v1.5 recommends this instruction on queries only; passages use no prefix.
_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load and cache the embedding model (loaded once per process)."""
    return SentenceTransformer(EMBED_MODEL)


def dimension() -> int:
    """Vector dimension of the loaded model (384 for bge-small-en-v1.5)."""
    return get_model().get_sentence_embedding_dimension()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed passage texts (no instruction prefix). Returns one vector each."""
    model = get_model()
    vectors = model.encode(list(texts), normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def embed_query(question: str) -> list[float]:
    """Embed a search query, with the bge retrieval instruction prefix."""
    model = get_model()
    vector = model.encode(_QUERY_PREFIX + question, normalize_embeddings=True)
    return vector.tolist()
