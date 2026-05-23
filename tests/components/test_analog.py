"""Analog component stub contract (NMOS / PMOS / Diode / OpAmp).

Scope A: pin metadata + bounds + graph-registration smoke only. No physics.
"""

from __future__ import annotations

from manim_engineering.components import NMOS, PMOS, Diode, OpAmp
from manim_engineering.core import CircuitGraph, PinDirection, SignalType


def test_nmos_pins_and_metadata() -> None:
    n = NMOS("m1", label="M1")
    assert n.semantic_type == "analog"
    assert set(n.pins) == {"gate", "drain", "source"}
    assert n.get_pin("gate").direction is PinDirection.IN
    assert n.get_pin("drain").direction is PinDirection.INOUT
    assert n.get_pin("source").direction is PinDirection.INOUT
    for name in ("gate", "drain", "source"):
        assert n.get_pin(name).signal_type is SignalType.ANALOG
    bounds = n.get_bounds()
    assert bounds.width > 0 and bounds.height > 0
    # NMOS source sits at the bottom-right corner, drain at top-right.
    anchors = n.anchor_points
    assert anchors["drain"][1] > anchors["source"][1]


def test_nmos_attaches_to_graph() -> None:
    graph = CircuitGraph()
    n = NMOS("m1")
    n.attach_to(graph)
    assert any(node.id == "m1" for node in graph.nodes)


def test_pmos_pins_and_swap_drain_source_roles() -> None:
    p = PMOS("p1", label="P1")
    assert p.semantic_type == "analog"
    assert set(p.pins) == {"gate", "drain", "source"}
    assert p.get_pin("gate").direction is PinDirection.IN
    for name in ("gate", "drain", "source"):
        assert p.get_pin(name).signal_type is SignalType.ANALOG
    # In CMOS-inverter convention the PMOS source sits at top, drain at bottom.
    anchors = p.anchor_points
    assert anchors["source"][1] > anchors["drain"][1]
    assert p.get_bounds().width > 0 and p.get_bounds().height > 0


def test_pmos_attaches_to_graph() -> None:
    graph = CircuitGraph()
    p = PMOS("p1")
    p.attach_to(graph)
    assert any(node.id == "p1" for node in graph.nodes)


def test_diode_pins_and_directions() -> None:
    d = Diode("d1", label="D1")
    assert d.semantic_type == "analog"
    assert set(d.pins) == {"anode", "cathode"}
    assert d.get_pin("anode").direction is PinDirection.IN
    assert d.get_pin("cathode").direction is PinDirection.OUT
    assert d.get_pin("anode").signal_type is SignalType.ANALOG
    assert d.get_pin("cathode").signal_type is SignalType.ANALOG
    assert d.get_bounds().width > 0 and d.get_bounds().height > 0


def test_diode_attaches_to_graph() -> None:
    graph = CircuitGraph()
    d = Diode("d1")
    d.attach_to(graph)
    assert any(node.id == "d1" for node in graph.nodes)


def test_op_amp_pins_and_directions() -> None:
    op = OpAmp("u1", label="U1")
    assert op.semantic_type == "analog"
    assert set(op.pins) == {"in_p", "in_n", "out"}
    assert op.get_pin("in_p").direction is PinDirection.IN
    assert op.get_pin("in_n").direction is PinDirection.IN
    assert op.get_pin("out").direction is PinDirection.OUT
    for name in ("in_p", "in_n", "out"):
        assert op.get_pin(name).signal_type is SignalType.ANALOG
    # Non-inverting input sits above inverting input.
    anchors = op.anchor_points
    assert anchors["in_p"][1] > anchors["in_n"][1]


def test_op_amp_attaches_to_graph() -> None:
    graph = CircuitGraph()
    op = OpAmp("u1")
    op.attach_to(graph)
    assert any(node.id == "u1" for node in graph.nodes)
