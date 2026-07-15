"""
Search — a question into its nearest knowledge chunks, metadata-reranked.

Pipeline position:

    question  ->  Search  ->  [most relevant + most important Markdown chunks]

Responsibility: retrieval only. It embeds the question, pulls a candidate pool by
semantic similarity, then reranks using the finding's FACTS (severity, validated,
scanner, host) so critical/validated items surface for severity questions —
semantic relevance alone under-ranks a terse "critical SQLi" against a chatty
banner. It does NOT know QdrantClient exists (that is index.py) and does NOT know
reasoning.md exists — retrieval is not reasoning.
"""

from __future__ import annotations

import re

from config import (
    BOOST_HOST,
    BOOST_NUCLEI,
    BOOST_VALIDATED,
    RERANK_CANDIDATES,
    RERANK_ENABLED,
    RERANK_SCALE,
    SEVERITY_BOOST,
    TOP_K,
)
from embeddings import embed, index

# IPv4 or dotted hostname mentioned in a question, for the host-match boost.
_HOST_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b")


def _question_hosts(question: str) -> set[str]:
    return set(_HOST_RE.findall(question.lower()))


def _boost(payload: dict, question_hosts: set[str]) -> float:
    """Raw importance boost from a finding's facts."""
    boost = SEVERITY_BOOST.get((payload.get("severity") or "").lower(), 0)
    if payload.get("validated"):
        boost += BOOST_VALIDATED
    if payload.get("scanner") == "nuclei":
        boost += BOOST_NUCLEI
    host = (payload.get("host") or "").lower()
    if host and any(h in host or host in h for h in question_hosts):
        boost += BOOST_HOST
    return boost


def search(question: str, top_k: int = TOP_K) -> list[dict]:
    """Return the top_k knowledge chunks most relevant AND most important.

    Each result carries its payload plus `semantic_score` (cosine), `boost` (raw
    metadata boost), and `score` (the combined value it was ranked by).
    """
    vector = embed.embed_query(question)
    pool = max(top_k, RERANK_CANDIDATES) if RERANK_ENABLED else top_k
    hits = index.search_points(vector, top_k=pool)

    if RERANK_ENABLED and hits:
        question_hosts = _question_hosts(question)
        for hit in hits:
            hit["semantic_score"] = hit.get("score", 0.0)
            hit["boost"] = _boost(hit, question_hosts)
            hit["score"] = hit["semantic_score"] + RERANK_SCALE * hit["boost"]
        hits.sort(key=lambda h: h["score"], reverse=True)

    return hits[:top_k]


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "which findings are most critical?"
    hits = search(question)
    if not hits:
        raise SystemExit("Nothing indexed yet. Run: python -m tools.genesis ingest")

    print(f"Query: {question}\n")
    for rank, hit in enumerate(hits, 1):
        print(
            f"{rank}. [{hit.get('score', 0):.3f}] {hit.get('finding_id')} "
            f"(sev={hit.get('severity')}, boost={hit.get('boost', 0)}, "
            f"semantic={hit.get('semantic_score', 0):.3f}) -> {hit.get('path')}"
        )
