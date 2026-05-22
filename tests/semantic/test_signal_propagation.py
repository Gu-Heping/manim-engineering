"""Signal direction metadata and explicit propagation."""

from __future__ import annotations

import pytest

from manim_engineering.semantic import (
    CircuitGraph,
    LogicLevel,
    LogicState,
    Node,
    PinDirection,
    PropagationError,
    PropagationState,
    Signal,
    SignalDirection,
    SignalType,
)


def _linked_graph() -> tuple[CircuitGraph, Node, Node]:
    graph = CircuitGraph()
    src = Node(id="src")
    dst = Node(id="dst")
    src.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)
    dst.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    graph.add_node(src)
    graph.add_node(dst)
    graph.connect(src.get_pin("out"), dst.get_pin("in"))
    return graph, src, dst


def test_signal_direction_metadata() -> None:
    sig = Signal(
        name="clk",
        signal_type=SignalType.CLOCK,
        direction=SignalDirection.FORWARD,
        timing_metadata={"period": 10.0, "duty": 0.5},
    )
    assert sig.direction == SignalDirection.FORWARD
    assert sig.source_pin is None
    assert sig.sink_pin is None
    assert sig.timing_metadata["period"] == 10.0


def test_explicit_propagation_updates_endpoints() -> None:
    graph, src, dst = _linked_graph()
    sig = Signal(
        name="data",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
        direction=SignalDirection.FORWARD,
    )
    out_pin = src.get_pin("out")
    in_pin = dst.get_pin("in")

    record = sig.propagate(out_pin, in_pin, graph=graph)

    assert record.from_pin_id == "src.out"
    assert record.to_pin_id == "dst.in"
    assert record.state_transition == "low→high"
    assert sig.source_pin == out_pin
    assert sig.sink_pin == in_pin
    assert sig.propagation_state == PropagationState.SETTLED
    assert isinstance(sig.value, LogicState)
    assert sig.value.level == LogicLevel.HIGH


def test_propagation_requires_topology_when_graph_given() -> None:
    graph, src, dst = _linked_graph()
    sig = Signal(name="x", signal_type=SignalType.DIGITAL)
    unconnected = Node(id="other")
    unconnected.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    graph.add_node(unconnected)
    with pytest.raises(PropagationError):
        sig.propagate(src.get_pin("out"), unconnected.get_pin("in"), graph=graph)


def test_propagation_history_is_ordered() -> None:
    graph, src, dst = _linked_graph()
    sig = Signal(
        name="seq",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    sig.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    sig.value = LogicState(level=LogicLevel.LOW)
    sig.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    assert len(sig.propagation_history) == 2
    assert sig.propagation_history[0].from_pin_id == "src.out"
