"""
Chunker — Markdown knowledge files into embedding-ready chunks.

Pipeline position:

    knowledge/findings/*.md  ->  Chunker  ->  [{id, text, metadata}, ...]

Responsibility: structure only. No embeddings, no Qdrant, no AI.

For the prototype, one finding file = one chunk. Each finding document is
already atomic (one host/service/finding), so there is nothing to split — no
LangChain, no recursive splitter. When large multi-section reports arrive later,
chunk_file() can return several chunks and nothing downstream changes, because
callers already iterate a list.
"""

from __future__ import annotations

from pathlib import Path

from config import KNOWLEDGE_DIR, ROOT

FINDINGS_DIR = KNOWLEDGE_DIR


def parse_frontmatter(markdown: str) -> tuple[dict, str]:
    """Split a document into its YAML front matter (flat dict) and body.

    The knowledge.md template emits simple `key: value` front matter, so a full
    YAML parser is unnecessary. Returns ({}, markdown) when there is no front
    matter.
    """
    if not markdown.startswith("---"):
        return {}, markdown

    lines = markdown.splitlines()
    try:
        end = next(i for i in range(1, len(lines))
                   if lines[i].strip() == "---")
    except StopIteration:
        return {}, markdown  # no closing delimiter; treat as bodyless

    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    body = "\n".join(lines[end + 1:]).strip()
    return meta, body


def _relative_path(path: Path) -> str:
    """Path relative to the project root when possible, else the raw path."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def chunk_file(path: str | Path) -> list[dict]:
    """Turn one Markdown finding file into a list of chunks (one, for now).

    A chunk is {id, text, metadata}. The full file text is embedded — the front
    matter carries searchable terms (host, service, severity, cve) worth keeping
    in the vector. Metadata is stored separately so it can be used as a payload
    filter later without re-reading Markdown.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    meta, _body = parse_frontmatter(text)

    finding_id = meta.get("finding_id") or path.stem
    chunk = {
        "id": finding_id,
        "text": text,
        "metadata": {
            "finding_id": finding_id,
            "host": meta.get("host", "unknown"),
            "service": meta.get("service", "unknown"),
            "severity": meta.get("severity", "unknown"),
            # scanner/tool/validated enable payload filtering later ("only nuclei
            # findings", "only validated") without re-reading Markdown.
            "scanner": meta.get("scanner", "unknown"),
            "tool": meta.get("tool", "unknown"),
            "validated": meta.get("validated", "").strip().lower() == "true",
            "path": _relative_path(path),
            "filename": path.name,
            "source": "knowledge",
        },
    }
    return [chunk]


def chunk_directory(findings_dir: str | Path = FINDINGS_DIR) -> list[dict]:
    """Chunk every Markdown file in a directory into a flat list of chunks."""
    findings_dir = Path(findings_dir)
    chunks: list[dict] = []
    for md in sorted(findings_dir.glob("*.md")):
        chunks.extend(chunk_file(md))
    return chunks
