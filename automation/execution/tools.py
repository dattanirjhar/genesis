"""
Central binary resolution for connector tools.

Bare tool names are ambiguous on this kind of setup:

  - `httpx`: the Python httpx library installs a CLI that shadows ProjectDiscovery
    httpx on PATH (especially inside an active venv). We must pick the go/bin one,
    not the venv one.
  - `whatweb`: often installed outside PATH (reachable only via a shell alias),
    which subprocess cannot resolve.

`resolve(tool_id)` returns the absolute path to the CORRECT binary, or None if it
cannot be found. Connectors build argv with the bare id; the executor rewrites
argv[0] via resolve() so the right binary always runs and missing tools fail
loudly instead of silently invoking the wrong one.

Override precedence: explicit override paths -> ~/go/bin (for go/PD tools) -> PATH.
Set GENESIS_TOOL_<ID> in the environment to force a specific path.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

GOBIN = Path.home() / "go" / "bin"

# Tools whose correct binary is NOT the first match on PATH.
_OVERRIDES: dict[str, list[Path]] = {
    "httpx": [GOBIN / "httpx"],                        # avoid the Python httpx CLI
    "whatweb": [Path.home() / "WhatWeb" / "whatweb"],  # installed outside PATH
}

# ProjectDiscovery / go tools: prefer ~/go/bin when present.
_PREFER_GOBIN = {"subfinder", "httpx", "nuclei", "katana", "naabu", "uncover", "gau"}


def _usable(path: Path) -> bool:
    return path.exists() and os.access(path, os.X_OK)


def resolve(tool_id: str) -> str | None:
    """Absolute path to the correct binary for a tool id, or None."""
    # 1. Environment override, e.g. GENESIS_TOOL_HTTPX=/opt/httpx
    env = os.environ.get(f"GENESIS_TOOL_{tool_id.upper()}")
    if env and _usable(Path(env)):
        return env

    # 2. Explicit override candidates
    for cand in _OVERRIDES.get(tool_id, []):
        if _usable(cand):
            return str(cand)

    # 3. Prefer ~/go/bin for go/PD tools
    if tool_id in _PREFER_GOBIN and _usable(GOBIN / tool_id):
        return str(GOBIN / tool_id)

    # 4. Fall back to PATH
    return shutil.which(tool_id)


def is_available(tool_id: str) -> bool:
    return resolve(tool_id) is not None


if __name__ == "__main__":
    # Diagnostic: verify every registered connector tool resolves.
    from automation.execution.registry import all_tools

    print("Tool resolution\n" + "-" * 15)
    missing = []
    for tool_id in sorted(all_tools()):
        path = resolve(tool_id)
        if path:
            print(f"  OK       {tool_id:<11} {path}")
        else:
            print(f"  MISSING  {tool_id}")
            missing.append(tool_id)

    ollama = shutil.which("ollama")
    print(f"\n  {'OK      ' if ollama else 'MISSING '} ollama      {ollama or ''}")
    if missing:
        print(f"\n{len(missing)} tool(s) not resolvable: {', '.join(missing)}")
