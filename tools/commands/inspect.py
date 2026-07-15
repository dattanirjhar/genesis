"""
Commands: inspect / inspect-json / inspect-chunk / inspect-vector / list.

Read-only views into what the pipeline produced, so you can debug without
browsing the filesystem.
"""

from __future__ import annotations

import json
from pathlib import Path

from config import COLLECTION_NAME
from embeddings import chunker, embed, index
from llm import knowledge_builder as kb
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR, RAW_DIR, find_chunk


def _flow() -> None:
    """Visualize how data moved through the pipeline, per producing tool."""
    raw = len([p for p in RAW_DIR.glob("*") if p.is_file()])
    per_tool: dict[str, int] = {}
    for doc in sorted(NORMALIZED_DIR.glob("*.json")):
        try:
            data = json.loads(doc.read_text())
        except (ValueError, OSError):
            continue
        tool = data.get("scan", {}).get("detected_tool", doc.stem)
        per_tool[tool] = per_tool.get(tool, 0) + len(data.get("findings", []))

    knowledge = len(list(FINDINGS_DIR.glob("*.md")))
    client = index.get_client()
    vectors = (client.get_collection(COLLECTION_NAME).points_count
               if client.collection_exists(COLLECTION_NAME) else 0)

    print("\nPipeline flow\n-------------")
    print(f"  data/raw            {raw} file(s)")
    print("       |  parser")
    if per_tool:
        for tool, n in sorted(per_tool.items(), key=lambda kv: -kv[1]):
            print(f"       +-- {tool:<12} {n} finding(s)")
    else:
        print("       (nothing parsed — run `ingest`)")
    print("       |  knowledge builder")
    print(f"  knowledge/findings  {knowledge} markdown")
    print("       |  embed + index")
    print(f"  qdrant              {vectors} vector(s)")
    if per_tool and knowledge != sum(per_tool.values()):
        print(f"\n  note: {sum(per_tool.values())} parsed findings but {knowledge} "
              f"markdown — some findings failed to build (check `ingest` output).")


def inspect(arg: str) -> None:
    """A finding by id, or the whole pipeline flow when called bare."""
    if not arg:
        _flow()
        return
    path = FINDINGS_DIR / f"{kb._safe_filename(arg)}.md"
    if not path.exists():
        print(f"  not found: {path.name}  (try `list`)")
        return
    text = path.read_text(encoding="utf-8")
    meta, _ = chunker.parse_frontmatter(text)
    print("\nMarkdown\n--------")
    print(text.rstrip())
    print("\nMetadata\n--------")
    for key, value in meta.items():
        print(f"  {key:<11}: {value}")


def inspect_json(arg: str) -> None:
    """Pretty-print one or all Canonical JSON documents."""
    files = sorted(NORMALIZED_DIR.glob("*.json"))
    if arg:
        files = [NORMALIZED_DIR / f"{Path(arg).stem}.json"]
    for path in files:
        if not path.exists():
            print(f"  not found: {path.name}")
            continue
        print(f"\n=== {path.name} ===")
        print(path.read_text(encoding="utf-8").rstrip())


def inspect_chunk(arg: str) -> None:
    """Show exactly what gets embedded for a finding: id, metadata, markdown."""
    chunk = find_chunk(arg)
    if not chunk:
        print(f"  no chunk with id: {arg}  (try `list`)")
        return
    print(f"\nChunk\n-----\nID: {chunk['id']}")
    print("\nMetadata\n--------")
    for key, value in chunk["metadata"].items():
        print(f"  {key:<11}: {value}")
    print("\nMarkdown (this exact text is embedded)\n" + "-" * 38)
    print(chunk["text"].rstrip())


def inspect_vector(arg: str) -> None:
    """Embed a finding's chunk and show its dimension + first components."""
    chunk = find_chunk(arg)
    if not chunk:
        print(f"  no chunk with id: {arg}  (try `list`)")
        return
    vector = embed.embed_texts([chunk["text"]])[0]
    preview = ", ".join(f"{x:+.4f}" for x in vector[:10])
    print(f"\nVector for {chunk['id']}")
    print(f"  dim: {len(vector)}")
    print(f"  first 10: [ {preview}, ... ]")


def list_findings(_: str = "") -> None:
    files = sorted(FINDINGS_DIR.glob("*.md"))
    if not files:
        print("  No knowledge yet. Run `rebuild`.")
        return
    print(f"\n{len(files)} finding(s):")
    for f in files:
        print(f"  - {f.stem}")


COMMANDS = {
    "inspect": inspect,
    "inspect-json": inspect_json,
    "inspect-chunk": inspect_chunk,
    "inspect-vector": inspect_vector,
    "list": list_findings,
}
