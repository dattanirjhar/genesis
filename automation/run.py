"""
Genesis automation entry point.

    python -m automation.run <target>              # show the execution graph (safe)
    python -m automation.run <target> --execute    # run the auto-run plan
    python -m automation.run <target> --execute --yes   # auto-approve intrusive tools

The planner derives an adaptive execution graph from typed tool capabilities:
tools that can run now form the plan; tools gated by a runtime signal-value
(e.g. technology=wordpress) are shown as conditional branches. The pipeline ends
at data/raw/ — the existing Genesis pipeline takes over from there, unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.execution import executor, registry  # noqa: E402
from automation.planner import planner  # noqa: E402


def _tags(approval: bool, installed: bool) -> str:
    parts = []
    if approval:
        parts.append("APPROVAL")
    if not installed:
        parts.append("not-installed")
    return f"  [{', '.join(parts)}]" if parts else ""


def _print_plan(plan) -> None:
    print(f"Target: {plan.target}   classified: {plan.kind}")
    print(f"Seed signals: {', '.join(sorted(plan.seeds))}\n")

    print("Execution plan (data-dependency order):")
    if not plan.steps:
        print("  (nothing runnable from these seeds)")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i:>2}. [{step.phase:<15}] {step.tool_id:<11}"
              f"{_tags(step.approval_required, step.installed)}")
        print(f"      {', '.join(step.consumes) or '(seed)'}  ->  "
              f"{', '.join(step.produces)}")

    if plan.branches:
        print("\nConditional branches (activate at runtime when the signal appears):")
        for b in plan.branches:
            by = f"  (from {', '.join(b.produced_by)})" if b.produced_by else ""
            print(f"  - {b.tool_id:<11} when {b.condition}{by}"
                  f"{_tags(b.approval_required, b.installed)}")

    if plan.unreachable:
        print("\nUnreachable (no tool produces what they need):")
        for u in plan.unreachable:
            print(f"  - {u.tool_id:<11} needs {', '.join(u.missing)}")

    print(f"\nKnowledge graph: {len(plan.graph)} capability nodes, "
          f"{len(plan.graph.edges())} edges "
          f"({', '.join(sorted(plan.graph.node_types()))})")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Genesis execution planner/runner.")
    ap.add_argument("target", help="URL, domain, IP, or CIDR")
    ap.add_argument("--execute", action="store_true",
                    help="actually run the auto-run plan (default: plan only)")
    ap.add_argument("--yes", action="store_true",
                    help="auto-approve intrusive tools when executing")
    args = ap.parse_args()

    plan = planner.build_plan(args.target)
    _print_plan(plan)

    if not args.execute:
        print("\nPlan only. Re-run with --execute to run tools (writes to data/raw/).")
        return 0

    tools = registry.all_tools()
    print("\nExecuting plan ...")
    for step in plan.steps:
        result = executor.execute(tools[step.tool_id], args.target,
                                  dry_run=False, approve=args.yes)
        print(f"  {step.tool_id}: {result['status']}  ({result['command']})")

    if plan.branches:
        print("\nConditional branches were not auto-run — they require runtime "
              "signals from parsed output (the adaptive execution loop).")
    print("\nDone. Raw artifacts are in data/raw/ — run the Genesis pipeline next "
          "(python -m tools.genesis rebuild).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
