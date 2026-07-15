"""
Command: doctor — preflight health check.

    Genesis> doctor

Verifies everything the pipeline needs before you waste time debugging a run:
Ollama + models, Qdrant, scanner binaries, wordlists, output folders, config.
Prints a check per line and a final READY / NOT READY verdict.
"""

from __future__ import annotations

import re
import subprocess

import requests

from automation.execution.tools import resolve
from config import (
    EMBED_MODEL,
    EXECUTION_DIR,
    KNOWLEDGE_DIR,
    MODEL_NAME,
    NORMALIZED_DIR,
    OLLAMA_URL,
    QDRANT_PATH,
    RAW_DIR,
    REPORTS_DIR,
    WORDLIST,
)

PASS, FAIL, WARN = "✓", "✗", "!"

# The version flag each tool actually accepts (they differ).
_VERSION_ARGS = {
    "nmap": ["--version"],
    "nuclei": ["-version"],
    "subfinder": ["-version"],
    "httpx": ["-version"],
    "katana": ["-version"],
    "naabu": ["-version"],
    "gobuster": ["--version"],
    "amass": ["-version"],
    "sqlmap": ["--version"],
    "nikto": ["-Version"],
    "whatweb": ["--version"],
}
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_VERSION = re.compile(r"v?\d+\.\d+(?:\.\d+)?")


def _check(symbol: str, label: str, detail: str = "") -> None:
    print(f"  {symbol} {label}" + (f"  ({detail})" if detail else ""))


def _tool_status(tool_id: str) -> tuple[str, str | None]:
    """Run the tool's version command to verify it actually works.

    Returns (state, detail): state is ok | missing | timeout | error.
    """
    path = resolve(tool_id)
    if not path:
        return "missing", None
    args = _VERSION_ARGS.get(tool_id, ["--version"])
    try:
        proc = subprocess.run([path, *args], capture_output=True, text=True, timeout=20)
    except subprocess.TimeoutExpired:
        return "timeout", None
    except OSError as exc:
        return "error", str(exc)[:40]
    output = _ANSI.sub("", (proc.stdout or "") + (proc.stderr or ""))
    match = _VERSION.search(output)
    return "ok", (match.group(0) if match else "runs")


def _ollama_models() -> list[str]:
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return [m["name"] for m in resp.json().get("models", [])]
    except (requests.RequestException, ValueError, KeyError):
        return []


def run(_: str = "") -> None:
    fails = 0
    warns = 0

    # --- config + folders --------------------------------------------------
    _check(PASS, "Config", f"model={MODEL_NAME}, embed={EMBED_MODEL.split('/')[-1]}")

    for label, path in [("data/raw", RAW_DIR), ("data/normalized", NORMALIZED_DIR),
                        ("knowledge/findings", KNOWLEDGE_DIR),
                        ("knowledge/reports", REPORTS_DIR),
                        ("execution", EXECUTION_DIR)]:
        path.mkdir(parents=True, exist_ok=True)
    _check(PASS, "Output folders", "present")

    # --- ollama + models ---------------------------------------------------
    models = _ollama_models()
    if models:
        _check(PASS, "Ollama", OLLAMA_URL)
        if any(m == MODEL_NAME or m.startswith(MODEL_NAME) for m in models):
            _check(PASS, "Reasoning model", MODEL_NAME)
        else:
            _check(FAIL, "Reasoning model", f"{MODEL_NAME} not pulled (ollama pull {MODEL_NAME})")
            fails += 1
    else:
        _check(FAIL, "Ollama", f"not reachable at {OLLAMA_URL} (run: ollama serve)")
        _check(FAIL, "Reasoning model", "unknown (Ollama down)")
        fails += 2

    # --- embedding model ---------------------------------------------------
    try:
        from embeddings import embed
        dim = embed.dimension()
        _check(PASS, "Embedding model", f"{EMBED_MODEL.split('/')[-1]} (dim {dim})")
    except Exception as exc:  # noqa: BLE001
        _check(FAIL, "Embedding model", str(exc)[:60])
        fails += 1

    # --- qdrant ------------------------------------------------------------
    try:
        from config import COLLECTION_NAME
        from embeddings import index
        client = index.get_client()
        pts = (client.get_collection(COLLECTION_NAME).points_count
               if client.collection_exists(COLLECTION_NAME) else 0)
        _check(PASS, "Qdrant", f"{QDRANT_PATH.name} ({pts} points)")
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        if "already accessed" in msg or "lock" in msg.lower():
            # Embedded Qdrant is single-process; another Genesis session has it.
            _check(WARN, "Qdrant", "in use by another Genesis process — close other consoles")
            warns += 1
        else:
            _check(FAIL, "Qdrant", msg[:60])
            fails += 1

    # --- scanner tools (verified by running each version command) ---------
    from automation.execution import registry
    print("  Scanner tools:")
    for tool_id in sorted(registry.all_tools()):
        state, detail = _tool_status(tool_id)
        if state == "ok":
            _check(f"  {PASS}", f"{tool_id:<11}", detail)
        elif state == "missing":
            _check(f"  {WARN}", f"{tool_id:<11}", "not installed")
            warns += 1
        else:
            _check(f"  {FAIL}", f"{tool_id:<11}", f"{state}" + (f": {detail}" if detail else ""))
            warns += 1

    # --- wordlists ---------------------------------------------------------
    if WORDLIST.exists():
        _check(PASS, "Wordlists", str(WORDLIST))
    else:
        _check(WARN, "Wordlists", f"not found: {WORDLIST} (gobuster needs one; set GENESIS_WORDLIST)")
        warns += 1

    # --- verdict -----------------------------------------------------------
    print()
    if fails:
        print(f"  NOT READY — {fails} failure(s)" + (f", {warns} warning(s)" if warns else ""))
    elif warns:
        print(f"  READY (with {warns} warning(s))")
    else:
        print("  READY")


COMMANDS = {"doctor": run}
