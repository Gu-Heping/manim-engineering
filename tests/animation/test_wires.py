"""Wire path helpers for animation."""

from __future__ import annotations

import pytest

from manim_engineering.animation.wires import (
    connection_id_for_pins,
    oriented_wire_points,
    wire_path_for_connection,
)
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.core import CircuitGraph


def test_connection_id_for_pins() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    conn_id = connection_id_for_pins(graph, r1.get_pin("b").id, r2.get_pin("a").id)
    assert conn_id == graph.connections[0].id


def test_oriented_wire_points_follow_propagation_direction() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    conn_id = graph.connections[0].id
    wire = wire_path_for_connection(layout, conn_id)
    ordered = oriented_wire_points(layout, wire, r1.get_pin("b").id, r2.get_pin("a").id)
    start = layout.pin_positions[r1.get_pin("b").id]
    assert ordered[0].x == pytest.approx(start.x)
    assert ordered[0].y == pytest.approx(start.y)
