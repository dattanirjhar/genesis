"""
Prompt loader — the only place that reads prompt files from disk.

client.py asks this module for a composed system prompt by task name; it never
touches file paths itself. Adding a new AI worker later means dropping a new
`<task>.md` into llm/prompts/ — no code changes here or in the client.

Prompt layers:

    system.md   ->  identity + safety rules (shared by every task)
    <task>.md   ->  the worker's job (knowledge, reasoning, report, ...)

`build_system(task)` returns  system.md + "\n\n" + <task>.md.
"""

from __future__ import annotations

from pathlib import Path

# llm/prompts/ resolved relative to this file, so it works regardless of the
# process's current working directory.
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "llm" / "prompts"


def load_prompt(name: str) -> str:
    """Read a single prompt file by name (without the .md extension)."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def build_system(task: str) -> str:
    """Compose the full system prompt for a task: identity + task instructions.

    Args:
        task: a worker name matching a file in llm/prompts/, e.g. "knowledge"
              or "reasoning".
    """
    return f"{load_prompt('system')}\n\n{load_prompt(task)}"
