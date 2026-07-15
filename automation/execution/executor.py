"""
Executor — the one place that actually runs a tool.

Everything else in the automation layer is planning and metadata. This is the
only module that touches subprocess, so replacing it with an MCP.run() call
later leaves the planner and every connector untouched.

Safe by default: dry_run=True builds and returns the command without running it.
Intrusive tools (approval_required) will not run unless explicitly approved.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime

from automation.execution.connectors.base import Tool
from automation.execution.tools import resolve
from config import EXECUTION_DIR, RAW_DIR


def _target_for(tool: Tool, target: str) -> str:
    """Give each tool the target form it expects.

    subfinder/amass want a registered domain; nmap/naabu want a bare host; web
    tools take the URL as given. Without this, a URL target would be handed to
    subfinder verbatim (which needs a domain).
    """
    from automation.planner import classifier
    if tool.id in ("subfinder", "amass"):
        return classifier.registered_domain(target) or classifier.hostname(target)
    if tool.id in ("nmap", "naabu"):
        return classifier.hostname(target)
    return target


def _log_run(tool: Tool, target: str, argv: list[str], started: str,
             exit_code: int, stdout: str, stderr: str, outputs: list[str]) -> str:
    """Write an auditable execution record to execution/scan_NNN.json."""
    EXECUTION_DIR.mkdir(parents=True, exist_ok=True)
    idx = len(list(EXECUTION_DIR.glob("scan_*.json"))) + 1
    path = EXECUTION_DIR / f"scan_{idx:03d}.json"
    path.write_text(json.dumps({
        "tool": tool.id,
        "target": target,
        "command": " ".join(argv),
        "started": started,
        "finished": datetime.now().isoformat(timespec="seconds"),
        "exit_code": exit_code,
        "stdout_size": len(stdout or ""),
        "stderr_size": len(stderr or ""),
        "stdout": (stdout or "")[-4000:],
        "stderr": (stderr or "")[-4000:],
        "artifacts": outputs,
        "signals_produced": list(tool.produces),
    }, indent=2), encoding="utf-8")
    return str(path)


def execute(tool: Tool, target: str, dry_run: bool = True, approve: bool = False) -> dict:
    """Run (or plan) one tool against a target. Returns a result dict.

    status is one of: dry-run | needs-approval | not-installed | ok | error.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    argv = tool.command(_target_for(tool, target))
    # Rewrite argv[0] to the resolved absolute path so the correct binary runs
    # (e.g. ProjectDiscovery httpx, not the venv's Python httpx CLI).
    binary = resolve(tool.id)
    if binary:
        argv = [binary, *argv[1:]]
    result = {
        "tool": tool.id,
        "command": " ".join(argv),
        "outputs": [str(RAW_DIR / o) for o in tool.outputs],
    }

    if dry_run:
        return {**result, "status": "dry-run"}

    if tool.approval_required and not approve:
        return {**result, "status": "needs-approval"}

    if binary is None:
        return {**result, "status": "not-installed"}

    started = datetime.now().isoformat(timespec="seconds")
    try:
        proc = subprocess.run(argv, capture_output=True, text=True,
                              timeout=tool.timeout)
        exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        status = "ok" if exit_code == 0 else "error"
    except subprocess.TimeoutExpired as exc:
        # A hung tool must not hang the pipeline; record what we got and move on.
        exit_code, stdout, stderr = -1, exc.stdout or "", (exc.stderr or "") + \
            f"\n[genesis] timed out after {tool.timeout}s"
        status = "timeout"

    log_path = _log_run(tool, target, argv, started, exit_code,
                        stdout if isinstance(stdout, str) else "",
                        stderr if isinstance(stderr, str) else "", result["outputs"])
    return {**result, "status": status, "returncode": exit_code, "log": log_path}
