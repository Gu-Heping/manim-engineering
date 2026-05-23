"""Deterministic CircuitGraph iteration and Connection.id ordering.

These tests live in ``tests/core/`` because they only exercise core topology
types (``CircuitGraph``, ``Node``, ``Connection``) plus the layer-internal
``connection_id_for_pins`` helper. They were previously in
``tests/semantic/test_determinism.py`` alongside a propagation test; that
file is split so each test lives next to the layer it actually exercises.
"""

from __future__ import annotations

from manim_engineering.animation.wires import connection_id_for_pins
from manim_engineering.components import Resistor
from manim_engineering.core import (
    CircuitGraph,
    Node,
    PinDirection,
    SignalType,
)


def test_graph_iteration_order_stable() -> None:
    graph = CircuitGraph()
    for node_id in ("z", "a", "m"):
        node = Node(id=node_id)
        node.add_pin("p", direction=PinDirection.OUT, signal_type=SignalType.SIGNAL)
        graph.add_node(node)
    node_ids = [n.id for n in graph.nodes]
    assert node_ids == ["a", "m", "z"]


def _two_resistor_graph() -> tuple[CircuitGraph, Resistor, Resistor]:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    return graph, r1, r2


def test_connection_id_deterministic_from_port_pair() -> None:
    graph, r1, r2 = _two_resistor_graph()
    conn = graph.connections[0]
    assert conn.id == "conn-r1.b--r2.a"
    assert conn.id == connection_id_for_pins(graph, r1.get_pin("b").id, r2.get_pin("a").id)


def test_connection_id_stable_on_graph_replay() -> None:
    def ids() -> tuple[str, ...]:
        graph, _, _ = _two_resistor_graph()
        return tuple(c.id for c in graph.connections)

    assert ids() == ids()


def test_connection_id_order_stable_with_two_nets() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    graph.connect(r1.get_pin("a"), r2.get_pin("b"))

    def ordered_ids() -> tuple[str, ...]:
        return tuple(c.id for c in graph.connections)

    assert ordered_ids() == ("conn-r1.a--r2.b", "conn-r1.b--r2.a")
    assert ordered_ids() == ordered_ids()
