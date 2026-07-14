"""
Search — a question into its nearest knowledge chunks.

Pipeline position:

    question  ->  Search  ->  [nearest Markdown chunks]

Responsibility: retrieval only. It embeds the question and asks the index for
the nearest vectors. It does NOT know QdrantClient exists (that is index.py) and
it does NOT know reasoning.md exists — retrieval is not reasoning. The reasoner
is a separate, later module that consumes what this returns.
"""

from __future__ import annotations

from config import TOP_K
from embeddings import embed, index


def search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top_k knowledge chunks most relevant to a question.

    Each result carries its stored payload (finding_id, host, service, severity,
    path, text) plus a similarity "score", highest first.
    """
    vector = embed.embed_query(question)
    return index.search_points(vector, top_k=top_k)


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "which hosts expose SSH?"
    hits = search(question)
    if not hits:
        raise SystemExit("Nothing indexed yet. Run: python -m embeddings.index")

    print(f"Query: {question}\n")
    for rank, hit in enumerate(hits, 1):
        print(
            f"{rank}. [{hit.get('score', 0):.3f}] {hit.get('finding_id')} "
            f"(host={hit.get('host')}, severity={hit.get('severity')}) "
            f"-> {hit.get('path')}"
        )
