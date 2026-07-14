"""
Commands: inspect / inspect-json / inspect-chunk / inspect-vector / list.

Read-only views into what the pipeline produced, so you can debug without
browsing the filesystem.
"""

from __future__ import annotations

from pathlib import Path

from embeddings import chunker, embed
from llm import knowledge_builder as kb
from tools.commands._common import FINDINGS_DIR, NORMALIZED_DIR, find_chunk


def inspect(arg: str) -> None:
    """Show a finding's Markdown and parsed metadata by finding_id."""
    if not arg:
        print("  usage: inspect <finding_id>   (see `list`)")
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
