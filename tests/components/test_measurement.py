"""Measurement component contracts."""

from __future__ import annotations

from manim_engineering.components import CurrentProbe, VoltageProbe
from manim_engineering.core import CircuitGraph
from manim_engineering.core.enums import PinDirection, SignalType


def test_measurement_package_exports_probe_components() -> None:
    import manim_engineering.components.measurement as measurement

    assert measurement.VoltageProbe is VoltageProbe
    assert measurement.CurrentProbe is CurrentProbe
    assert "VoltageProbe" in measurement.__all__
    assert "CurrentProbe" in measurement.__all__


def test_voltage_probe_exposes_differential_sense_ports() -> None:
    probe = VoltageProbe("vp1", label="Vout")

    assert probe.semantic_type == "measurement"
    assert set(probe.pins) == {"pos", "neg"}
    assert probe.port_pos is probe.get_port("pos")
    assert probe.port_neg is probe.get_port("neg")
    assert probe.port_pos.direction is PinDirection.IN
    assert probe.port_neg.direction is PinDirection.IN
    assert {pin.signal_type for pin in probe.pins.values()} == {SignalType.ANALOG}
    assert probe.anchor_points["pos"] == (0.0, 0.68)
    assert probe.anchor_points["neg"] == (0.0, 0.32)


def test_current_probe_exposes_inline_terminals() -> None:
    probe = CurrentProbe("ip1", label="Iload")

    assert probe.semantic_type == "measurement"
    assert set(probe.pins) == {"in", "out"}
    assert probe.port_in is probe.get_port("in")
    assert probe.port_out is probe.get_port("out")
    assert probe.port_in.direction is PinDirection.INOUT
    assert probe.port_out.direction is PinDirection.INOUT
    assert {pin.signal_type for pin in probe.pins.values()} == {SignalType.ANALOG}
    assert probe.anchor_points["in"] == (0.0, 0.5)
    assert probe.anchor_points["out"] == (1.0, 0.5)


def test_measurement_probe_connects_in_circuit_graph() -> None:
    graph = CircuitGraph()
    current = CurrentProbe("ip1")
    voltage = VoltageProbe("vp1")
    graph.add(current)
    graph.add(voltage)

    connection = graph.connect(current.port_out, voltage.port_pos)

    assert connection.port_a is current.port_out
    assert connection.port_b is voltage.port_pos
    assert graph.are_connected(current.port_out, voltage.port_pos)
