"""Core CircuitGraph API: add(element) and connect(port_a, port_b)."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.core import (
    CircuitGraph,
    ConnectionState,
    PortDirection,
    SignalType,
)


def test_circuit_graph_add_and_connect_ports() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)

    circuit.connect(r1.get_port("b"), r2.get_port("a"))

    assert circuit.are_connected(r1.get_port("b"), r2.get_port("a"))
    assert r1.get_port("b").connection_state == ConnectionState.CONNECTED


def test_port_alias_equals_pin() -> None:
    from manim_engineering.core import Pin, Port

    assert Pin is Port


def test_node_ports_and_pins_views() -> None:
    from manim_engineering.core import Node

    node = Node(id="u1")
    port = node.add_port("out", direction=PortDirection.OUT, signal_type=SignalType.DIGITAL)
    assert node.get_port("out") is port
    assert node.get_pin("out") is port
    assert node.pins["out"] is port
