"""Digital logic gate component contracts."""

from __future__ import annotations

from manim_engineering.components import ANDGate, NOTGate, ORGate
from manim_engineering.core import CircuitGraph
from manim_engineering.core.enums import PinDirection, SignalType


def test_digital_package_exports_gate_components() -> None:
    import manim_engineering.components.digital as digital

    assert digital.ANDGate is ANDGate
    assert digital.ORGate is ORGate
    assert digital.NOTGate is NOTGate
    assert "ANDGate" in digital.__all__
    assert "ORGate" in digital.__all__
    assert "NOTGate" in digital.__all__


def test_binary_digital_gates_expose_semantic_ports() -> None:
    for gate_cls in (ANDGate, ORGate):
        gate = gate_cls("g1", label="G")

        assert gate.semantic_type == "digital_gate"
        assert gate.bounds.width == 1.0
        assert gate.bounds.height == 0.8
        assert set(gate.pins) == {"a", "b", "out"}
        assert gate.port_a is gate.get_port("a")
        assert gate.port_b is gate.get_port("b")
        assert gate.port_out is gate.get_port("out")
        assert gate.port_a.direction is PinDirection.IN
        assert gate.port_b.direction is PinDirection.IN
        assert gate.port_out.direction is PinDirection.OUT
        assert {pin.signal_type for pin in gate.pins.values()} == {SignalType.DIGITAL}
        assert gate.anchor_points["a"] == (0.0, 0.72)
        assert gate.anchor_points["b"] == (0.0, 0.28)
        assert gate.anchor_points["out"] == (1.0, 0.5)


def test_not_gate_exposes_inverter_ports() -> None:
    gate = NOTGate("inv", label="INV")

    assert gate.semantic_type == "digital_gate"
    assert set(gate.pins) == {"in", "out"}
    assert gate.port_in is gate.get_port("in")
    assert gate.port_out is gate.get_port("out")
    assert gate.port_in.direction is PinDirection.IN
    assert gate.port_out.direction is PinDirection.OUT
    assert {pin.signal_type for pin in gate.pins.values()} == {SignalType.DIGITAL}
    assert gate.anchor_points["in"] == (0.0, 0.5)
    assert gate.anchor_points["out"] == (1.0, 0.5)


def test_digital_gates_connect_in_circuit_graph() -> None:
    graph = CircuitGraph()
    and_gate = ANDGate("and1")
    inv = NOTGate("inv1")
    graph.add(and_gate)
    graph.add(inv)

    connection = graph.connect(and_gate.port_out, inv.port_in)

    assert connection.port_a is and_gate.port_out
    assert connection.port_b is inv.port_in
    assert graph.are_connected(and_gate.port_out, inv.port_in)
