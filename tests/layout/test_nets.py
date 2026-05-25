"""Electrical net grouping and star routing tests."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import (
    MIN_VISIBLE_STUB,
    LayoutEngine,
    group_connections_into_nets,
    net_id_for_pins,
)
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.nets import connection_for_wire
from manim_engineering.layout.types import Point2D


def _three_pin_net_graph():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r3 = Resistor("r3", label="R3")
    for element in (r1, r2, r3):
        element.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    graph.connect(r2.get_pin("a"), r3.get_pin("a"))
    return graph, {"r1": r1, "r2": r2, "r3": r3}


def test_group_connections_into_nets_merges_shared_pins() -> None:
    graph, _elements = _three_pin_net_graph()
    nets = group_connections_into_nets(graph.connections)
    assert len(nets) == 1
    assert nets[0].pin_ids == frozenset({"r1.b", "r2.a", "r3.a"})
    assert nets[0].net_id == net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))


def test_star_routing_uses_single_vertical_trunk() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    layout = LayoutEngine().layout(
        graph,
        elements,
        net_waypoints={net_id: hub},
    )
    vertical_at_hub = [
        wire
        for wire in layout.wires
        if any(
            seg.start.x == seg.end.x == hub.x and seg.start.y != seg.end.y
            for seg in wire.segments
        )
    ]
    assert vertical_at_hub


def test_star_net_hub_coincident_pin_gets_visible_stub() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    r2 = elements["r2"]
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides={r2.element_id: origin_for_pin_at(r2, "a", hub)},
        net_waypoints={net_id: hub},
    )
    hub_branch = next(
        wire for wire in layout.wires if wire.connection_id == f"{net_id}/r2.a"
    )
    assert len(hub_branch.segments) == 1
    seg = hub_branch.segments[0]
    length = abs(seg.end.x - seg.start.x) + abs(seg.end.y - seg.start.y)
    assert length >= MIN_VISIBLE_STUB - 1e-6


def test_connection_for_wire_resolves_net_branch_ids() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    layout = LayoutEngine().layout(
        graph,
        elements,
        net_waypoints={net_id: hub},
    )
    connections = {connection.id: connection for connection in graph.connections}
    net_wires = [wire for wire in layout.wires if wire.connection_id.startswith("net-")]
    assert net_wires
    for wire in net_wires:
        connection = connection_for_wire(wire, connections)
        assert connection.id in connections
