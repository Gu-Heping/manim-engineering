"""CircuitElement base and graph integration tests."""

from __future__ import annotations

import pytest

from manim_engineering.components import CircuitElement, Resistor
from manim_engineering.components.exceptions import InvalidBoundsError
from manim_engineering.components.types import Bounds
from manim_engineering.core import (
    CircuitGraph,
    ConnectionState,
    PinDirection,
    SignalType,
)
from manim_engineering.semantic import InvalidPinError


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


def test_nmos_gate_drain_source_can_connect() -> None:
    """NMOS drain/source (INOUT) must connect through ``CircuitGraph`` like Resistor."""
    from manim_engineering.components import NMOS, Resistor

    graph = CircuitGraph()
    n = NMOS("m1")
    r = Resistor("r1")
    n.attach_to(graph)
    r.attach_to(graph)

    # source ↔ resistor terminal (both INOUT, compatible).
    conn = graph.connect(n.get_pin("source"), r.get_pin("a"))
    assert conn.involves(n.get_pin("source"))
    assert graph.are_connected(n.get_pin("source"), r.get_pin("a"))
    assert n.get_pin("source").connection_state == ConnectionState.CONNECTED


def test_input_driver_fanouts_to_two_gates() -> None:
    """``InputDriver.out`` may fan out to PMOS+NMOS gates without conflict.

    Mirrors the CMOS inverter input net pattern: a single OUT pin drives two
    IN pins (gates). Guards the canonical inverter topology against accidental
    re-tightening of the connection-direction rules.
    """
    from manim_engineering.components import NMOS, PMOS, InputDriver

    graph = CircuitGraph()
    drv = InputDriver("in1")
    p = PMOS("p1")
    n = NMOS("n1")
    drv.attach_to(graph)
    p.attach_to(graph)
    n.attach_to(graph)

    c1 = graph.connect(drv.get_pin("out"), p.get_pin("gate"))
    c2 = graph.connect(drv.get_pin("out"), n.get_pin("gate"))
    assert c1.id != c2.id


def test_analog_signal_propagates_through_nmos() -> None:
    """``SignalType.ANALOG`` round-trips through ``Signal.propagate`` without
    triggering the LOW→HIGH digital-edge promotion in ``_resolve_propagated_value``.

    Guards the "原样拷贝" branch flagged as a risk in the Scope A plan: an
    ANALOG signal with ``LogicState(LOW)`` should remain LOW after propagation
    (no auto-toggle), and ``propagation_history`` should record one record.
    """
    from manim_engineering.components import NMOS, Resistor
    from manim_engineering.semantic import LogicLevel, LogicState, Signal

    graph = CircuitGraph()
    n = NMOS("m1")
    r = Resistor("r1")
    n.attach_to(graph)
    r.attach_to(graph)
    graph.connect(n.get_pin("source"), r.get_pin("a"))

    sig = Signal(
        name="vsrc",
        signal_type=SignalType.ANALOG,
        value=LogicState(level=LogicLevel.LOW),
    )
    record = sig.propagate(n.get_pin("source"), r.get_pin("a"), graph=graph)

    assert record.from_pin_id == "m1.source"
    assert record.to_pin_id == "r1.a"
    assert isinstance(sig.value, LogicState)
    # ANALOG signals do NOT auto-toggle LOW→HIGH (only DIGITAL/CLOCK/DATA do).
    assert sig.value.level == LogicLevel.LOW
    assert len(sig.propagation_history) == 1
