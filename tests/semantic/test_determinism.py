"""Deterministic graph and propagation ordering."""

from __future__ import annotations

from manim_engineering.semantic import (
    CircuitGraph,
    LogicLevel,
    LogicState,
    Node,
    PinDirection,
    Signal,
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


def test_repeated_propagation_same_result() -> None:
    graph = CircuitGraph()
    a = Node(id="a")
    b = Node(id="b")
    a.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)
    b.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    graph.add_node(a)
    graph.add_node(b)
    graph.connect(a.get_pin("out"), b.get_pin("in"))

    def run_once() -> str:
        sig = Signal(
            name="s",
            signal_type=SignalType.DIGITAL,
            value=LogicState(level=LogicLevel.LOW),
        )
        rec = sig.propagate(a.get_pin("out"), b.get_pin("in"), graph=graph)
        return rec.state_transition

    assert run_once() == run_once()
