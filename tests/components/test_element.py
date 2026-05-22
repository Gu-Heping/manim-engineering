"""CircuitElement base and graph integration tests."""

from __future__ import annotations

import pytest

from manim_engineering.components import CircuitElement, Resistor
from manim_engineering.components.exceptions import InvalidBoundsError
from manim_engineering.components.types import Bounds
from manim_engineering.semantic import (
    CircuitGraph,
    ConnectionState,
    InvalidPinError,
    PinDirection,
    SignalType,
)


def test_resistor_construction_and_pins() -> None:
    r = Resistor("r1", label="R1")
    assert r.label == "R1"
    assert r.semantic_type == "passive"
    assert set(r.pins) == {"a", "b"}
    assert r.get_pin("a").id == "r1.a"
    assert r.get_pin("a").direction == PinDirection.INOUT
    assert r.get_pin("a").signal_type == SignalType.SIGNAL


def test_resistor_bounds_and_anchors() -> None:
    r = Resistor("r1")
    bounds = r.get_bounds()
    assert bounds.width > 0
    assert bounds.height > 0
    assert "a" in r.anchor_points
    assert "b" in r.anchor_points
    assert "center" in r.anchor_points


def test_get_pin_unknown_raises() -> None:
    r = Resistor("r1")
    with pytest.raises(InvalidPinError):
        r.get_pin("missing")


def test_invalid_bounds_raises() -> None:
    with pytest.raises(InvalidBoundsError):
        Bounds(width=0.0, height=1.0)


def test_two_resistors_connect_via_graph() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)

    conn = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    assert conn.involves(r1.get_pin("b"))
    assert graph.are_connected(r1.get_pin("b"), r2.get_pin("a"))
    assert r1.get_pin("b").connection_state == ConnectionState.CONNECTED
    assert r2.get_pin("a").connection_state == ConnectionState.CONNECTED
    assert graph.neighbors(r1.get_pin("b")) == (r2.get_pin("a"),)


def test_to_node_shares_pin_instances() -> None:
    r = Resistor("r1")
    node = r.to_node()
    assert node.get_pin("a") is r.get_pin("a")


def test_circuit_element_is_abstract() -> None:
    with pytest.raises(TypeError):
        CircuitElement("x")  # type: ignore[abstract]
