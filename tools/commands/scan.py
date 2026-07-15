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

from automation.execution import executor, registry
from automation.planner import planner


def run(arg: str = "") -> None:
    parts = arg.split()
    if not parts:
        print("  usage: scan <target> [--deep] [--yes] [--plan]")
        print("    --deep  include enrichment tools (gobuster)")
        print("    --yes   include intrusive tools (nuclei, sqlmap)")
        print("    --plan  show the plan without running anything")
        return

    target = parts[0]
    approve = "--yes" in parts
    deep = "--deep" in parts
    plan_only = "--plan" in parts

    tools = registry.all_tools()
    plan = planner.build_plan(target)
    print(f"  Target: {target}   (classified: {plan.kind})")
    if not plan.steps:
        print("  No runnable tools for this target.")
        return

    labels = [s.tool_id + ("*" if tools[s.tool_id].optional else "")
              for s in plan.steps]
    print(f"  Plan: {' -> '.join(labels)}   (* = enrichment, needs --deep)")
    if plan.branches:
        print(f"  Branches (activate at runtime): {', '.join(b.tool_id for b in plan.branches)}")

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
