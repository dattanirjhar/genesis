"""
Reasoner — grounded security analysis from a question plus retrieved knowledge.

Pipeline position:

    question  ->  Search  ->  relevant Markdown  ->  Reasoner  ->  grounded answer

Single responsibility:

    question + retrieved knowledge  ->  answer

Nothing more. This is not a chatbot. It answers ONE question against the evidence
that retrieval already surfaced, in the Answer / Evidence / Confidence / Next
step format defined by reasoning.md.

Hard boundaries:

  - The reasoner NEVER searches. It calls embeddings.search to obtain hits; it
    does not know QdrantClient or embeddings exist beyond that one call. If it
    ever queried the vector store directly, the architecture would be broken.
  - The reasoner NEVER parses. It has no idea XML, JSON, or Markdown files
    exist. It receives context strings and produces an answer.

The only collaborators are search (retrieve) and llm.client.chat (reason).
Prompt composition (system.md + reasoning.md) is handled inside the client.
"""

from __future__ import annotations

from config import TOP_K
from embeddings import search
from llm.client import chat


def build_context(hits: list[dict]) -> str:
    """Format retrieved chunks into a labeled context block for the prompt.

    This is where most of the engineering is: the model wants clearly separated,
    labeled findings — not a list of dicts. Each block names the finding and its
    key attributes, then includes the finding's Markdown verbatim.
    """
    if not hits:
        return "No relevant findings were retrieved from the knowledge base."

    blocks = []
    for i, hit in enumerate(hits, 1):
        header = (
            f"=== Finding {i}: {hit.get('finding_id', 'unknown')} "
            f"(host={hit.get('host', 'unknown')}, "
            f"service={hit.get('service', 'unknown')}, "
            f"severity={hit.get('severity', 'unknown')}) ==="
        )
        body = (hit.get("text") or "").strip()
        blocks.append(f"{header}\n{body}")
    return "\n\n".join(blocks)


def answer_with_sources(question: str, top_k: int = TOP_K) -> dict:
    """Answer a question and return the answer alongside the sources used.

    Steps: retrieve -> build context -> reason. Returns
    {"question", "answer", "sources"} so a caller (e.g. the UI) can show which
    findings grounded the answer.
    """
    hits = search.search(question, top_k=top_k)
    context = build_context(hits)
    prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{question}"
    response = chat(prompt=prompt, task="reasoning")
    return {"question": question, "answer": response, "sources": hits}


def answer(question: str, top_k: int = TOP_K) -> str:
    """Answer a question and return just the grounded answer text."""
    return answer_with_sources(question, top_k=top_k)["answer"]


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) or "Which hosts expose SSH?"
    result = answer_with_sources(question)

    print(f"QUESTION: {result['question']}\n")
    print(result["answer"])
    print("\n--- sources ---")
    for hit in result["sources"]:
        print(f"  [{hit.get('score', 0):.3f}] {hit.get('finding_id')} ({hit.get('path')})")
