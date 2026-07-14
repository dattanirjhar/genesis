"""
Interactive, step-by-step walkthrough of the Genesis pipeline.

Runs each stage against the REAL project directories and pauses on [ENTER]
between stages, so you can open the files that were just written and inspect
them before moving on:

    Raw scanner output
        -> [ENTER] -> Canonical JSON      (data/normalized/)
        -> [ENTER] -> Markdown Knowledge  (knowledge/findings/)
        -> [ENTER] -> Chunks
        -> [ENTER] -> Embeddings
        -> [ENTER] -> Qdrant Index        (rag/qdrant_db/)
        -> [ENTER] -> Semantic Retrieval  (shown BEFORE the LLM)
        -> [ENTER] -> Reasoner            -> Grounded Answer

Usage (from the project root):

    python test_walkthrough.py                 # full paced walkthrough
    python test_walkthrough.py --stage parser  # run one stage and exit
    python test_walkthrough.py --stage qa       # jump straight to Q&A

Stages: parser, knowledge, chunk, embed, index, qa

Requirements: Ollama running (knowledge + reasoning); the embedding model
downloads on first use.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the project importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import COLLECTION_NAME, EMBED_MODEL, QDRANT_PATH, TOP_K  # noqa: E402
from embeddings import chunker, embed, index, search  # noqa: E402
from llm import knowledge_builder as kb  # noqa: E402
from llm import reasoner  # noqa: E402
from llm.client import is_available  # noqa: E402
from parser import parser as parser_mod  # noqa: E402

# Real pipeline directories (module defaults — no redirection).
RAW_DIR = parser_mod.RAW_DIR
NORMALIZED_DIR = parser_mod.OUT_DIR
FINDINGS_DIR = kb.FINDINGS_DIR


# --- presentation helpers --------------------------------------------------

def header(step: str, title: str) -> None:
    print("\n" + "=" * 72)
    print(f"[{step}]  {title}")
    print("=" * 72)


def pause(msg: str = "\n   [ENTER] to continue to the next stage ...") -> None:
    """Wait for the user. In a non-interactive shell, continue instead of hang."""
    try:
        input(msg)
    except EOFError:
        print("   (non-interactive input; continuing)")


# --- stages ----------------------------------------------------------------

def stage_parser() -> None:
    header("1/6", "PARSER  —  raw scanner output -> Canonical JSON")
    raw_files = [p for p in sorted(RAW_DIR.glob("*")) if p.is_file()]
    print(f"   Input: {RAW_DIR}")
    for f in raw_files:
        print(f"     - {f.name}")

    total = 0
    print()
    for src in raw_files:
        try:
            doc = parser_mod.parse_file(src)
            out = parser_mod.parse_and_save(src)
            total += len(doc["findings"])
            print(
                f"   {src.name}: detected={doc['scan']['detected_tool']}, "
                f"hosts={len(doc['hosts'])}, findings={len(doc['findings'])} "
                f"-> data/normalized/{out.name}"
            )
        except Exception as exc:  # noqa: BLE001 - show, don't abort the walkthrough
            print(f"   {src.name}: skipped ({exc})")

    print(f"\n   -> {total} canonical finding(s) written to {NORMALIZED_DIR}")
    print("   Open data/normalized/*.json to inspect the scanner-independent contract.")


def stage_knowledge() -> None:
    header("2/6", "KNOWLEDGE BUILDER  —  Canonical JSON -> Markdown (LLM)")
    docs = sorted(NORMALIZED_DIR.glob("*.json"))
    if not docs:
        print("   No normalized JSON yet. Run the parser stage first.")
        return

    written = failed = 0
    for doc_path in docs:
        print(
            f"   Reading {doc_path.name} ... building (one LLM call per finding)")
        summary = kb.process_document(doc_path)
        written += len(summary["written"])
        failed += len(summary["failed"])

    print(
        f"\n   -> {written} markdown file(s) in {FINDINGS_DIR}  (failed: {failed})")
    for md in sorted(FINDINGS_DIR.glob("*.md")):
        print(f"     - {md.name}")
    print("   Open knowledge/findings/*.md and read the generated knowledge.")


def stage_chunk() -> list[dict]:
    header("3/6", "CHUNKER  —  Markdown -> chunks (one finding = one chunk)")
    md_count = len(list(FINDINGS_DIR.glob("*.md")))
    chunks = chunker.chunk_directory()
    print(f"   Markdown files: {md_count}")
    print(f"   Chunks produced: {len(chunks)}")
    for c in chunks:
        print(f"     - {c['id']}")

    if chunks:
        c = chunks[0]
        preview = c["text"].replace("\n", " ")[:160]
        print("\n   Chunk preview")
        print("   ------------------------------------------")
        print(f"   id:       {c['id']}")
        print(f"   metadata: {c['metadata']}")
        print(f"   text:     {preview} ...")
    return chunks


def stage_embed() -> None:
    header("4/6", "EMBEDDER  —  chunks -> vectors (CPU)")
    chunks = chunker.chunk_directory()
    if not chunks:
        print("   No chunks. Build knowledge first.")
        return

    print(f"   Embedding model: {EMBED_MODEL}")
    print(f"   Dimension:       {embed.dimension()}")
    vectors = embed.embed_texts([c["text"] for c in chunks])
    print(f"   Vectors created: {len(vectors)}")

    preview = ", ".join(f"{x:+.4f}" for x in vectors[0][:10])
    print("\n   Vector preview (first 10 of "
          f"{len(vectors[0])} dims of '{chunks[0]['id']}')")
    print(f"     [ {preview}, ... ]")


def stage_index() -> None:
    header("5/6", "QDRANT INDEX  —  vectors + payload -> embedded Qdrant")
    chunks = chunker.chunk_directory()
    if not chunks:
        print("   No chunks. Build knowledge first.")
        return

    indexed = index.index_chunks(chunks)
    points = index.get_client().get_collection(COLLECTION_NAME).points_count
    print(f"   Collection: {COLLECTION_NAME}")
    print(f"   Indexed this run: {indexed}")
    print(f"   Points in collection: {points}")
    print(
        f"   Payload fields: {', '.join(sorted(chunks[0]['metadata'].keys()))}")

    print(f"\n   Qdrant database on disk: {QDRANT_PATH}")
    qpath = Path(QDRANT_PATH)
    if qpath.exists():
        for item in sorted(qpath.rglob("*"))[:12]:
            print(f"     {item.relative_to(qpath.parent)}")
    print("   Inspect rag/qdrant_db/ — you never edit these files by hand.")


def stage_qa() -> None:
    header("6/6", "RETRIEVAL + REASONING  —  ask your own questions")
    print("   Retrieval is shown BEFORE the LLM, so you can see whether the")
    print("   right findings were pulled. Empty line or 'quit' to exit.\n")

    while True:
        try:
            question = input("   Question > ").strip()
        except EOFError:
            break
        if not question or question.lower() in {"quit", "exit", "q"}:
            break

        # --- retrieval (deterministic, no LLM) -----------------------------
        hits = search.search(question, top_k=TOP_K)
        print(
            f"\n   --- Semantic retrieval: top {len(hits)} [before the LLM] ---")
        if not hits:
            print("   (nothing indexed, or no matches)\n")
            continue
        for rank, h in enumerate(hits, 1):
            print(
                f"   {rank}. [{h.get('score', 0):.3f}] {h.get('finding_id')} "
                f"(host={h.get('host')}, service={h.get('service')}, "
                f"severity={h.get('severity')})"
            )

        pause("\n   [ENTER] to run the reasoner on these findings ...")

        # --- reasoning (LLM) ----------------------------------------------
        print("\n   Building prompt and calling the reasoner (Qwen) ...")
        result = reasoner.answer_with_sources(question, top_k=TOP_K)
        print("\n   === GROUNDED ANSWER ===")
        for line in result["answer"].splitlines():
            print(f"   | {line}")
        print()


STAGES = {
    "parser": stage_parser,
    "knowledge": stage_knowledge,
    "chunk": stage_chunk,
    "embed": stage_embed,
    "index": stage_index,
    "qa": stage_qa,
}


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Step-by-step Genesis pipeline walkthrough.")
    ap.add_argument("--stage", choices=[*STAGES, "all"], default="all",
                    help="run a single stage and exit (default: full paced walkthrough)")
    args = ap.parse_args()

    if not is_available():
        print("WARNING: Ollama is not reachable. Knowledge building and reasoning "
              "will fail; parser/chunk/embed/index still work.\n")

    if args.stage != "all":
        STAGES[args.stage]()
        return 0

    print("GENESIS PIPELINE WALKTHROUGH")
    print("Raw -> Canonical JSON -> Markdown -> Chunks -> Vectors -> Qdrant "
          "-> Retrieval -> Reasoner")

    stage_parser()
    pause()
    stage_knowledge()
    pause()
    stage_chunk()
    pause()
    stage_embed()
    pause()
    stage_index()
    pause()
    stage_qa()

    print("\nWalkthrough complete. The directories above are yours to inspect.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
