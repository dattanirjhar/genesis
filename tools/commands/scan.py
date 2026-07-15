"""
Command: scan — run the planned tools against a target, into data/raw.

    Genesis> scan http://testphp.vulnweb.com          # default path
    Genesis> scan http://testphp.vulnweb.com --deep   # + enrichment tools (gobuster)
    Genesis> scan http://testphp.vulnweb.com --yes    # + intrusive (nuclei, sqlmap)
    Genesis> scan http://testphp.vulnweb.com --plan    # show the plan, run nothing

This is the front of the workflow: scan -> ingest -> reason -> report. It uses
the automation planner to decide which tools apply to the target, then runs the
runnable ones (each logged to execution/). Intrusive tools require --yes;
enrichment tools (e.g. gobuster) require --deep.
"""

from __future__ import annotations

import socket

from automation.execution import executor, registry
from automation.planner import classifier, planner


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _raw_ip_recon_note(target: str) -> None:
    """For an IP + --recon: verify web ports and explain the subdomain limit.

    A raw IP has no DNS name, so passive subdomain enumeration (subfinder/amass)
    cannot run. We check 80/443 directly so the analyst knows whether there is a
    web service to assess, and how to enumerate virtual hosts instead.
    """
    host = classifier.hostname(target)
    open_ports = [p for p in (80, 443) if _port_open(host, p)]

    print(f"\n  Note: {host} is a raw IP.")
    print("        Passive subdomain enumeration (subfinder/amass) needs a domain "
          "name and is skipped.")
    if open_ports:
        print(f"        Web ports open: {', '.join(map(str, open_ports))} — "
              "proceeding with web recon (whatweb/katana/nuclei) on the IP.")
    else:
        print("        Ports 80/443 appear CLOSED — no HTTP(S) service to assess "
              "here.")
        print("        To find virtual hosts, provide the domain name, or use "
              "vhost fuzzing against this IP.")


def run(arg: str = "") -> None:
    parts = arg.split()
    if not parts:
        print("  usage: scan <target> [--recon] [--deep] [--yes] [--plan]")
        print("    --recon  full web footprint (subfinder/amass/httpx on the domain)")
        print("    --deep   include enrichment tools (gobuster)")
        print("    --yes    include intrusive tools (nuclei, sqlmap)")
        print("    --plan   show the plan without running anything")
        return

    target = parts[0]
    approve = "--yes" in parts
    deep = "--deep" in parts
    plan_only = "--plan" in parts
    scope = "full" if ("--recon" in parts or "--full" in parts) else "targeted"
    if "--scope" in parts:
        i = parts.index("--scope")
        if i + 1 < len(parts):
            scope = parts[i + 1]

    tools = registry.all_tools()
    plan = planner.build_plan(target, scope=scope)
    print(f"  Target: {target}   (classified: {plan.kind}, scope: {plan.scope})")
    if not plan.steps:
        print("  No runnable tools for this target.")
        return

    labels = [s.tool_id + ("*" if tools[s.tool_id].optional else "")
              for s in plan.steps]
    print(f"  Plan: {' -> '.join(labels)}   (* = enrichment, needs --deep)")
    if plan.branches:
        print(f"  Branches (activate at runtime): {', '.join(b.tool_id for b in plan.branches)}")

    # A raw IP with --recon can't do passive subdomain enumeration; verify web
    # ports and explain, so the analyst knows what recon actually happened.
    if scope in ("full", "recon") and classifier.is_ip(target):
        _raw_ip_recon_note(target)

    if plan_only:
        print("  (--plan) nothing executed.")
        return

    print()
    ran = 0
    for step in plan.steps:
        tool = tools[step.tool_id]
        if not step.installed:
            print(f"  - {tool.id:<10} skipped (not installed)")
            continue
        if tool.optional and not deep:
            print(f"  - {tool.id:<10} skipped (enrichment; add --deep to run)")
            continue
        if step.approval_required and not approve:
            print(f"  - {tool.id:<10} skipped (intrusive; add --yes to run)")
            continue
        print(f"  - {tool.id:<10} running ...", flush=True)
        res = executor.execute(tool, target, dry_run=False, approve=approve)
        arts = ", ".join(a.split("/")[-1] for a in res.get("outputs", []))
        print(f"    -> {res['status']}" + (f"  ({arts})" if arts else ""))
        if res["status"] in ("ok", "error"):
            ran += 1

    print(f"\n  {ran} tool(s) ran. Raw artifacts in data/raw/.  Next: ingest")


COMMANDS = {"scan": run}
