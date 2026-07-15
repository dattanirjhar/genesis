"""
Knowledge graph — the interface the planner reasons over.

This is deliberately a thin in-memory implementation behind a stable API:

    add_node(type, value=None, **attrs)   # a capability instance (Host, Endpoint, ...)
    add_edge(src_id, dst_id, rel)          # provenance / lineage between capabilities
    has(type, value=None)                  # does any node of this type (value) exist?
    find(type, value=None)                 # nodes matching a type (and value)

The planner and connectors depend ONLY on these four methods. Tonight they wrap a
dict; later this same interface can be backed by Neo4j / Memgraph / ArangoDB
without changing the planner, the connectors, or the parsers.

Nodes use the capability vocabulary (automation.execution.signals): a bare type
node ("technology") is a placeholder the planner simulates during planning, while
a value node ("technology" with value "wordpress") is created at runtime from
parsed tool output — which is what lets conditional branches fire.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    id: str
    type: str
    value: str | None = None
    attrs: dict = field(default_factory=dict)


@dataclass
class Edge:
    src: str
    dst: str
    rel: str


class KnowledgeGraph:
    """In-memory capability graph behind a storage-agnostic API."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    def add_node(self, type: str, value: str | None = None, **attrs) -> Node:
        """Add (or merge into) a capability node. Returns the node."""
        node_id = f"{type}={value}" if value is not None else type
        existing = self._nodes.get(node_id)
        if existing is not None:
            existing.attrs.update(attrs)
            return existing
        node = Node(id=node_id, type=type, value=value, attrs=dict(attrs))
        self._nodes[node_id] = node
        return node

    def add_edge(self, src_id: str, dst_id: str, rel: str = "enriches") -> None:
        self._edges.append(Edge(src_id, dst_id, rel))

    def has(self, type: str, value: str | None = None) -> bool:
        """True if a node of this type (and value, if given) exists."""
        if value is None:
            return any(n.type == type for n in self._nodes.values())
        return f"{type}={value}" in self._nodes

    def find(self, type: str, value: str | None = None) -> list[Node]:
        """All nodes of a type, optionally filtered by value."""
        return [
            n for n in self._nodes.values()
            if n.type == type and (value is None or n.value == value)
        ]

    def node_types(self) -> set[str]:
        return {n.type for n in self._nodes.values()}

    def nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def edges(self) -> list[Edge]:
        return list(self._edges)

    def __len__(self) -> int:
        return len(self._nodes)
