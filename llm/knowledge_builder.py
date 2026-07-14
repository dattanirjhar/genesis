"""
Knowledge Builder — Canonical JSON findings into a Markdown knowledge base.

Pipeline position:

    Canonical JSON  ->  Knowledge Builder  ->  Markdown

This worker knows ONLY the Canonical JSON contract. It has no idea whether a
finding originally came from Nmap, Nuclei, Amass, or anything else — that concern
lives entirely in the parser. Its single responsibility is:

    load a normalized document
        -> iterate its findings
        -> ask the LLM to turn each finding into Markdown
        -> write one Markdown file per finding

It does not embed, retrieve, reason, or generate reports. Those are other
modules. If logic here ever needs to know a scanner format or touch a vector
store, it is in the wrong module.

The LLM is reached only through llm.client.chat(task="knowledge"). Prompt
composition (system.md + knowledge.md) is handled there; this module never reads
a prompt file.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from llm.client import chat

logger = logging.getLogger(__name__)

# Paths resolved relative to the project root, so behaviour does not depend on
# the process's current working directory.
ROOT = Path(__file__).resolve().parent.parent
NORMALIZED_DIR = ROOT / "data" / "normalized"
FINDINGS_DIR = ROOT / "knowledge" / "findings"

# Characters allowed in a derived filename. finding_id is a canonical identifier
# and may legitimately contain URL characters (":", "/"), so it must be
# sanitized before it becomes a path — deterministically, so the same id always
# maps to the same file.
_UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]")


# --- small helpers ---------------------------------------------------------

def _safe_filename(finding_id: str) -> str:
    """Map a canonical finding_id to a filesystem-safe, deterministic stem."""
    return _UNSAFE_FILENAME.sub("_", finding_id)


def _strip_code_fences(text: str) -> str:
    """Remove a wrapping ``` fence if the model added one.

    knowledge.md forbids code fences, but small models occasionally wrap their
    output anyway. An unnoticed fence would push the YAML front matter off the
    first line and corrupt the document. This is defensive cleanup of LLM
    output, not format parsing.
    """
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    lines = lines[1:]  # drop the opening ``` / ```markdown line
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]  # drop the closing fence
    return "\n".join(lines).strip()


# --- core steps ------------------------------------------------------------

def load_document(path: str | Path) -> dict:
    """Load one Canonical JSON document from disk.

    Raises ValueError if the file is not a Canonical JSON document (i.e. has no
    "findings" list), so callers fail clearly rather than silently doing nothing.
    """
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        document = json.load(fh)
    if "findings" not in document:
        raise ValueError(f"{path} is not a Canonical JSON document (no 'findings').")
    return document


def build_markdown(finding: dict) -> str:
    """Turn one Canonical JSON finding into Markdown via the LLM.

    The finding is serialized to JSON and handed to the "knowledge" task. The
    client composes the full prompt and returns the model's Markdown reply.

    JSON is serialized compactly (no indentation): the whitespace costs prompt
    tokens and the model does not need it.
    """
    prompt = json.dumps(finding, separators=(",", ":"))
    markdown = chat(prompt=prompt, task="knowledge")
    return _strip_code_fences(markdown)


# Sections the knowledge.md template must produce. Their absence signals the
# model ignored the template rather than a merely thin finding.
REQUIRED_SECTIONS = ("## Summary", "## Evidence", "## Impact", "## Recommendation")


def validate_markdown(markdown: str) -> None:
    """Reject malformed LLM Markdown before it enters the knowledge base.

    A document missing its YAML front matter or required sections usually means
    the model hallucinated the format. Catching it here keeps half-formed output
    from silently poisoning the knowledge base; the caller logs and skips the
    finding. Raises ValueError describing what is wrong.
    """
    if not markdown.startswith("---"):
        raise ValueError("missing YAML front matter (does not start with '---')")
    if "\n---" not in markdown:
        raise ValueError("YAML front matter is not closed")

    missing = [section for section in REQUIRED_SECTIONS if section not in markdown]
    if missing:
        raise ValueError(f"missing required section(s): {', '.join(missing)}")


def save_markdown(finding_id: str, markdown: str) -> Path:
    """Write Markdown to knowledge/findings/<finding_id>.md.

    The filename is derived deterministically from finding_id, so re-running the
    builder overwrites the same file rather than accumulating duplicates.
    """
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = FINDINGS_DIR / f"{_safe_filename(finding_id)}.md"
    path.write_text(markdown + "\n", encoding="utf-8")
    return path


# --- orchestration ---------------------------------------------------------

def process_document(path: str | Path) -> dict:
    """Build and save Markdown for every finding in one document.

    Findings are processed independently: if one fails (LLM error, write error,
    missing id, ...) it is logged and skipped, and the remaining findings still
    run. One bad finding must never abort the whole document.

    Returns a summary: {"document", "written": [Path], "failed": [finding_id]}.
    """
    document = load_document(path)
    findings = document.get("findings", [])

    written: list[Path] = []
    failed: list[str] = []

    logger.info("Processing %d finding(s) from %s", len(findings), Path(path).name)
    for finding in findings:
        finding_id = finding.get("finding_id")
        if not finding_id:
            logger.error("Skipping finding with no finding_id: %r", finding)
            failed.append("<missing finding_id>")
            continue

        try:
            markdown = build_markdown(finding)
            validate_markdown(markdown)  # gate: never save malformed Markdown
            out = save_markdown(finding_id, markdown)
            written.append(out)
            logger.info("  wrote %s", out.name)
        except Exception as exc:  # noqa: BLE001 - isolate one finding's failure
            logger.error("  failed %s: %s", finding_id, exc)
            failed.append(finding_id)

    return {"document": str(path), "written": written, "failed": failed}


def process_directory(normalized_dir: str | Path = NORMALIZED_DIR) -> list[dict]:
    """Process every Canonical JSON document in a directory.

    A document that fails to load is logged and skipped so one broken file does
    not stop the batch. Returns one summary per document processed.
    """
    normalized_dir = Path(normalized_dir)
    summaries: list[dict] = []
    for src in sorted(normalized_dir.glob("*.json")):
        try:
            summaries.append(process_document(src))
        except Exception as exc:  # noqa: BLE001 - isolate one document's failure
            logger.error("Failed to process %s: %s", src.name, exc)
    return summaries


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    args = sys.argv[1:]
    if args:
        summaries = []
        for target in args:
            try:
                summaries.append(process_document(target))
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to process %s: %s", target, exc)
    else:
        summaries = process_directory()

    total_written = sum(len(s["written"]) for s in summaries)
    total_failed = sum(len(s["failed"]) for s in summaries)
    print(f"\nDone: {total_written} markdown file(s) written, {total_failed} failed.")