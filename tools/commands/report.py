"""
Command: report — draft an assessment report from the knowledge base.

    knowledge/findings/*.md  ->  report  ->  knowledge/reports/genesis_report.md

    Genesis> report          # Markdown report (default)
    Genesis> report docx     # Word document
    Genesis> report md --llm # Markdown + reasoner-drafted executive summary

The executive summary can be drafted by the reasoner (--llm), grounding the
report in the same RAG pipeline as the analyst Q&A.
"""

from __future__ import annotations

from config import KNOWLEDGE_DIR
from report import report as report_mod


def run(arg: str = "") -> None:
    args = arg.split()
    fmt = "docx" if "docx" in args else "md"
    use_llm = "--llm" in args

    if not list(KNOWLEDGE_DIR.glob("*.md")):
        print("  No knowledge to report on. Run `ingest` first.")
        return

    summary = None
    if use_llm:
        print("  Drafting executive summary via the reasoner ...")
        summary = report_mod._llm_executive_summary()

    if fmt == "docx":
        out = report_mod.build_report(exec_summary=summary)
    else:
        out = report_mod.build_markdown_report(exec_summary=summary)
    print(f"  Report written: {out}")


COMMANDS = {"report": run}
