"""
Command: doctor — preflight health check.

    Genesis> doctor

Verifies everything the pipeline needs before you waste time debugging a run:
Ollama + models, Qdrant, scanner binaries, wordlists, output folders, config.
Prints a check per line and a final READY / NOT READY verdict.
"""

from __future__ import annotations

import requests

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


def _check(symbol: str, label: str, detail: str = "") -> None:
    print(f"  {symbol} {label}" + (f"  ({detail})" if detail else ""))


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
        _check(FAIL, "Qdrant", str(exc)[:60])
        fails += 1

    # --- scanner binaries --------------------------------------------------
    from automation.execution import registry
    from automation.execution.tools import resolve
    missing = [t for t in sorted(registry.all_tools()) if resolve(t) is None]
    if not missing:
        _check(PASS, "Scanner binaries", f"{len(registry.all_tools())} resolved")
    else:
        _check(WARN, "Scanner binaries", f"missing: {', '.join(missing)}")
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
