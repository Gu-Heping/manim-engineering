"""Graph-aware component ordering for left-to-right placement."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.graph import CircuitGraph


def placement_order_for_graph(
    graph: CircuitGraph,
    elements: Mapping[str, CircuitElement],
) -> tuple[CircuitElement, ...]:
    """
    Order elements for ``place_on_grid`` along explicit connect(port_a, port_b) flow.

    Each connection places ``port_a``'s owner before ``port_b``'s owner (left→right).
    Unconnected nodes append in stable ``element_id`` order.
    """
    ordered_ids: list[str] = []
    seen: set[str] = set()
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = defaultdict(int)

    node_ids = {node.id for node in graph.nodes}
    for node_id in node_ids:
        indegree.setdefault(node_id, 0)

    for connection in graph.connections:
        from_id = connection.port_a.owner_id
        to_id = connection.port_b.owner_id
        if from_id not in node_ids or to_id not in node_ids:
            continue
        outgoing[from_id].append(to_id)
        indegree[to_id] += 1
        indegree.setdefault(from_id, indegree.get(from_id, 0))

    for from_id in sorted(outgoing):
        outgoing[from_id] = sorted(set(outgoing[from_id]))

    queue = sorted(node_id for node_id in node_ids if indegree[node_id] == 0)
    while queue:
        node_id = queue.pop(0)
        if node_id in seen:
            continue
        seen.add(node_id)
        ordered_ids.append(node_id)
        for next_id in outgoing[node_id]:
            indegree[next_id] -= 1
            if indegree[next_id] == 0:
                queue.append(next_id)
                queue.sort()

    for node_id in sorted(node_ids - seen):
        ordered_ids.append(node_id)

    return tuple(elements[node_id] for node_id in ordered_ids if node_id in elements)
