"""InputDriver: single-pin OUT marker contract.

Scope A: pin metadata + graph-registration + downstream-connect smoke. No
physics; visual symbol coverage lives in tests/renderers/test_minimal_renderer.
"""

from __future__ import annotations

from manim_engineering.components import InputDriver, NMOS, PMOS
from manim_engineering.core import CircuitGraph, PinDirection, SignalType


def test_input_driver_default_pins_and_signal_type() -> None:
    d = InputDriver("in1", label="IN")
    assert d.semantic_type == "io"
    assert d.label == "IN"
    assert set(d.pins) == {"out"}
    out = d.get_pin("out")
    assert out.direction is PinDirection.OUT
    assert out.signal_type is SignalType.ANALOG
    assert d.signal_type is SignalType.ANALOG
    bounds = d.get_bounds()
    assert bounds.width > 0 and bounds.height > 0
    # Anchor convention: ``out`` sits at the right edge so wires exit horizontally.
    assert d.anchor_points["out"] == (1.0, 0.5)


def test_input_driver_digital_signal_type_override() -> None:
    d = InputDriver("din", signal_type=SignalType.DIGITAL)
    assert d.signal_type is SignalType.DIGITAL
    assert d.get_pin("out").signal_type is SignalType.DIGITAL


def test_input_driver_attaches_to_graph() -> None:
    graph = CircuitGraph()
    d = InputDriver("in1")
    d.attach_to(graph)
    assert any(node.id == "in1" for node in graph.nodes)


def test_input_driver_drives_single_gate() -> None:
    """``InputDriver.out`` (OUT) connects to an NMOS gate (IN) without errors."""
    graph = CircuitGraph()
    drv = InputDriver("in1")
    n = NMOS("m1")
    drv.attach_to(graph)
    n.attach_to(graph)

    conn = graph.connect(drv.get_pin("out"), n.get_pin("gate"))
    assert conn.involves(drv.get_pin("out"))
    assert graph.are_connected(drv.get_pin("out"), n.get_pin("gate"))


def test_input_driver_fanouts_to_two_gates() -> None:
    """One OUT pin may fan out to PMOS and NMOS gates (CMOS inverter pattern)."""
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
    assert graph.are_connected(drv.get_pin("out"), p.get_pin("gate"))
    assert graph.are_connected(drv.get_pin("out"), n.get_pin("gate"))
    # Both gates should report as connected.
    neighbors = set(p.id for p in graph.neighbors(drv.get_pin("out")))
    assert {"p1.gate", "n1.gate"}.issubset(neighbors)
