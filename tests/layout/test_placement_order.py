"""Graph-aware placement order (left→right along connect flow)."""

from __future__ import annotations

from manim_engineering.components import Capacitor, Resistor
from manim_engineering.layout import LayoutEngine, placement_order_for_graph
from manim_engineering.semantic import CircuitGraph


def test_placement_order_r1_before_c1() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    graph.add(r1)
    graph.add(c1)
    graph.connect(r1.port_b, c1.port_a)
    elements = {"r1": r1, "c1": c1}

    ordered = placement_order_for_graph(graph, elements)
    assert [element.element_id for element in ordered] == ["r1", "c1"]

    layout = LayoutEngine().layout(graph, elements)
    assert layout.placements[0].element_id == "r1"
    assert layout.placements[1].element_id == "c1"
    assert layout.placements[0].origin.x < layout.placements[1].origin.x
