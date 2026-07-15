"""
Planner — derive an execution graph from typed tool capabilities.

    target -> seed capability nodes -> fixpoint over consumes/produces

The planner reasons entirely through the KnowledgeGraph API (has/find/add_node);
it never touches storage and never names a tool statically. Starting from the
target's seed capabilities, it repeatedly runs any tool whose consumed
capabilities exist and whose `when` value-conditions hold, adding that tool's
produced capabilities (and provenance edges) — until nothing new can run.

Three outcomes per tool:
  - plan:        consumes present, no unmet value-condition -> auto-run
  - branch:      consumes present but gated by a value-condition (when=...) that
                 only appears at runtime -> conditional branch
  - unreachable: a consumed capability is never produced by anything reachable

Planning never executes anything; it simulates produced capability *types* as
placeholder nodes. Value nodes (technology=wordpress) appear only at runtime from
parsed output — which is exactly why branches are conditional here and adaptive
at execution time. Swapping the in-memory graph for a database changes nothing
in this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from automation.execution import registry
from automation.execution import signals as sig
from automation.graph.graph import KnowledgeGraph
from automation.planner import classifier


@dataclass
class PlannedStep:
    tool_id: str
    phase: str
    consumes: tuple[str, ...]
    produces: tuple[str, ...]
    approval_required: bool
    installed: bool


@dataclass
class Branch:
    tool_id: str
    phase: str
    condition: str            # value-condition that must hold, e.g. technology=wordpress
    produced_by: list[str]    # tools that can produce the condition's capability
    approval_required: bool
    installed: bool


@dataclass
class Unreachable:
    tool_id: str
    missing: list[str]


@dataclass
class Plan:
    target: str
    kind: str
    seeds: set[str]
    steps: list[PlannedStep]
    branches: list[Branch]
    unreachable: list[Unreachable]
    scope: str = "targeted"
    graph: KnowledgeGraph = field(default_factory=KnowledgeGraph)


def _condition_met(graph: KnowledgeGraph, condition: str) -> bool:
    type_, value = sig.parse(condition)
    return graph.has(type_, value)


def build_plan(target: str, scope: str = "targeted") -> Plan:
    tools = registry.all_tools()
    order = list(tools.values())  # deterministic registry order
    producers = registry.producers()

    graph = KnowledgeGraph()
    seeds = classifier.seed_signals(target, scope)
    for seed in seeds:
        graph.add_node(seed)

    completed: set[str] = set()
    steps: list[PlannedStep] = []

    # Fixpoint: run any newly-eligible tool until nothing changes.
    changed = True
    while changed:
        changed = False
        for tool in order:
            if tool.id in completed:
                continue
            if not all(graph.has(c) for c in tool.consumes):
                continue
            if tool.when and not all(_condition_met(graph, w) for w in tool.when):
                continue  # gated by a value-condition -> a branch, handled below

            steps.append(PlannedStep(tool.id, tool.phase, tool.consumes,
                                     tool.produces, tool.approval_required,
                                     tool.is_installed()))
            completed.add(tool.id)
            # Simulate outputs: add produced capability nodes + provenance edges.
            for produced in tool.produces:
                graph.add_node(produced)
                for consumed in tool.consumes:
                    graph.add_edge(consumed, produced, rel=tool.id)
            changed = True

    # Whatever didn't make the plan is a branch or unreachable.
    branches: list[Branch] = []
    unreachable: list[Unreachable] = []
    for tool in order:
        if tool.id in completed:
            continue
        missing = [c for c in tool.consumes if not graph.has(c)]
        if not missing and tool.when:
            for condition in tool.when:
                if not _condition_met(graph, condition):
                    type_, _ = sig.parse(condition)
                    branches.append(Branch(tool.id, tool.phase, condition,
                                           producers.get(type_, []),
                                           tool.approval_required,
                                           tool.is_installed()))
        else:
            unreachable.append(Unreachable(tool.id, missing or list(tool.when)))

    return Plan(target, classifier.classify(target), seeds,
                steps, branches, unreachable, scope, graph)
