"""
End-to-end smoke test for the full Genesis pipeline.

Drives every module in the architecture, exactly in the order of the design:

    INGEST      raw scanner outputs (Nmap XML, Nuclei JSONL, Amass JSONL)
      -> parser (detector + canonical + per-tool parsers)  -> Canonical JSON
    KNOWLEDGE   knowledge_builder                            -> Markdown per finding
    ENGINE      chunker -> embed -> index (Qdrant) -> search -> relevant findings
    AI          reasoner -> llm.client.chat(task="reasoning")-> grounded answer

Everything runs against a throwaway temp workspace (each module's output dir is
redirected there), so the real data/, knowledge/, and rag/ directories are never
touched. Real code paths are exercised — real parser, real LLM calls, real
embedding model, real embedded Qdrant — not mocks.

Requirements: Ollama running (for knowledge building + reasoning) and network on
first run (to download the embedding model into the HF cache).

Run from the project root:

    python -m tests.e2e_smoke        # or:  python tests/e2e_smoke.py
"""

from __future__ import annotations

import json
import logging
import shutil
import sys
import tempfile
from pathlib import Path

# Make the project importable whether run as a module or a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import COLLECTION_NAME  # noqa: E402
from embeddings import chunker, index, search  # noqa: E402
from llm import knowledge_builder as kb  # noqa: E402
from llm import reasoner  # noqa: E402
from llm.client import is_available  # noqa: E402
from parser import parser as parser_mod  # noqa: E402

# Keep worker INFO logs quiet; this script prints its own staged report.
logging.basicConfig(level=logging.WARNING)


# --- three raw scanner outputs (INGEST layer), one per real parser ----------

FIXTURES = {
    "scan_nmap.xml": """<?xml version="1.0"?>
<nmaprun scanner="nmap" args="nmap -sV 10.0.0.5" start="1700000000" startstr="Test">
  <host endtime="1700000100">
    <status state="up"/>
    <address addr="10.0.0.5" addrtype="ipv4"/>
    <hostnames><hostname name="target.local" type="user"/></hostnames>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="7.2" extrainfo="Ubuntu"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http" product="Apache httpd" version="2.4.52"/>
      </port>
    </ports>
  </host>
</nmaprun>
""",
    "scan_nuclei.jsonl": (
        '{"template-id":"git-config-exposure","info":{"name":"Exposed .git config",'
        '"severity":"medium","description":"A .git/config file is publicly exposed."},'
        '"host":"10.0.0.5","port":"80","type":"http",'
        '"matched-at":"http://10.0.0.5/.git/config"}\n'
    ),
    "scan_amass.jsonl": (
        '{"name":"www.example.com","domain":"example.com",'
        '"addresses":[{"ip":"93.184.216.34"}],"tag":"dns","sources":["DNS"]}\n'
    ),
}

# Expected: nmap yields 2 open-port findings, nuclei 1, amass 1.
EXPECTED_FINDINGS = 4

REASONING_QUESTION = "Which host is running an outdated SSH server, and what version is it?"


# --- tiny assertion reporter ------------------------------------------------

_failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"   {'PASS' if ok else 'FAIL'}  {label}" + (f"  ({detail})" if detail else ""))
    if not ok:
        _failures.append(label)


def banner(title: str) -> None:
    print(f"\n===== {title} =====")


# --- the pipeline run -------------------------------------------------------

def run(workspace: Path) -> None:
    raw_dir = workspace / "raw"
    normalized_dir = workspace / "normalized"
    findings_dir = workspace / "knowledge" / "findings"
    qdrant_dir = workspace / "qdrant"
    raw_dir.mkdir(parents=True)

    # Redirect every module's output at the temp workspace.
    parser_mod.OUT_DIR = normalized_dir
    kb.FINDINGS_DIR = findings_dir
    index.QDRANT_PATH = str(qdrant_dir)
    index.get_client.cache_clear()

    for name, content in FIXTURES.items():
        (raw_dir / name).write_text(content, encoding="utf-8")

    # --- INGEST -> Canonical JSON ------------------------------------------
    banner("INGEST  ->  parser  ->  Canonical JSON")
    detected: dict[str, int] = {}
    for src in sorted(raw_dir.glob("*")):
        doc = parser_mod.parse_file(src)
        parser_mod.parse_and_save(src)
        tool = doc["scan"]["detected_tool"]
        detected[tool] = len(doc["findings"])
        print(f"   {src.name}: detected={tool}, findings={len(doc['findings'])}")
    total_findings = sum(detected.values())
    check("all three scanner formats detected", set(detected) == {"nmap", "nuclei", "amass"},
          ", ".join(sorted(detected)))
    check(f"parsed {EXPECTED_FINDINGS} canonical findings", total_findings == EXPECTED_FINDINGS,
          f"got {total_findings}")

    # --- KNOWLEDGE -> Markdown ---------------------------------------------
    banner("KNOWLEDGE  ->  knowledge_builder  ->  Markdown per finding")
    written = 0
    failed = 0
    for doc_path in sorted(normalized_dir.glob("*.json")):
        summary = kb.process_document(doc_path)
        written += len(summary["written"])
        failed += len(summary["failed"])
    md_files = sorted(findings_dir.glob("*.md"))
    check("one Markdown file per finding", len(md_files) == EXPECTED_FINDINGS,
          f"{len(md_files)} files")
    check("no findings failed to build", failed == 0, f"{failed} failed")
    well_formed = all(
        f.read_text().startswith("---") and "## Summary" in f.read_text()
        for f in md_files
    )
    check("every Markdown file is well-formed", well_formed)

    # --- ENGINE: chunk -> embed -> index -----------------------------------
    banner("ENGINE  ->  chunker -> embed -> index -> Qdrant")
    chunks = chunker.chunk_directory(findings_dir)
    check("one chunk per finding", len(chunks) == EXPECTED_FINDINGS, f"{len(chunks)} chunks")
    indexed = index.index_chunks(chunks)
    points = index.get_client().get_collection(COLLECTION_NAME).points_count
    check("all chunks indexed into Qdrant", points == EXPECTED_FINDINGS, f"{points} points")
    # deterministic ids: re-index must not duplicate
    index.index_chunks(chunks)
    points_after = index.get_client().get_collection(COLLECTION_NAME).points_count
    check("re-index is idempotent (deterministic ids)", points_after == points,
          f"{points_after} points")

    # --- ENGINE: search ----------------------------------------------------
    banner("ENGINE  ->  search  ->  relevant findings")
    hits = search.search("outdated SSH server that needs patching", top_k=4)
    top = hits[0] if hits else {}
    print(f"   top hit: {top.get('finding_id')} (score={top.get('score', 0):.3f})")
    check("search returns hits", bool(hits), f"{len(hits)} hits")
    check("most relevant hit is the SSH finding", top.get("service") == "ssh",
          top.get("finding_id", "none"))

    # --- AI: reasoner ------------------------------------------------------
    banner("AI  ->  reasoner  ->  grounded security answer")
    result = reasoner.answer_with_sources(REASONING_QUESTION)
    answer = result["answer"]
    print(f"   Q: {REASONING_QUESTION}\n")
    for line in answer.splitlines():
        print(f"   | {line}")
    print()
    check("reasoner produced an answer", bool(answer.strip()))
    check("answer cites sources", bool(result["sources"]), f"{len(result['sources'])} sources")
    grounded = ("10.0.0.5" in answer) or ("7.2" in answer)
    check("answer is grounded in the evidence (mentions host or version)", grounded)


def main() -> int:
    if not is_available():
        print("Ollama is not reachable. Start it, then re-run this test.")
        return 2

    workspace = Path(tempfile.mkdtemp(prefix="genesis_e2e_"))
    print(f"Workspace: {workspace}")
    try:
        run(workspace)
    finally:
        # get_client holds a lock on the temp Qdrant dir; ignore_errors handles it.
        shutil.rmtree(workspace, ignore_errors=True)

    banner("RESULT")
    if _failures:
        print(f"   FAILED: {len(_failures)} check(s) -> {', '.join(_failures)}")
        return 1
    print("   ALL STAGES PASSED — full pipeline verified end to end.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
