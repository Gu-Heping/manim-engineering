"""Waveform derivation from semantic signal state."""

from __future__ import annotations

from manim_engineering.core import (
    CircuitGraph,
    Node,
    PinDirection,
    SignalType,
)
from manim_engineering.semantic import (
    LogicLevel,
    LogicState,
    Signal,
    TimingEdge,
)
from manim_engineering.waveform import (
    derive_bundle_from_signals,
    derive_trace_from_signal,
    level_from_value,
    timing_events_from_propagation,
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


def test_trace_starts_from_propagation_previous_value() -> None:
    graph, src, dst = _linked_graph()
    signal = Signal(
        name="data",
        signal_type=SignalType.DATA,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    trace = derive_trace_from_signal(signal)
    assert len(trace.samples) >= 2
    assert trace.samples[0].level == LogicLevel.LOW
    assert trace.samples[-1].level == LogicLevel.HIGH


def test_after_propagate_waveform_matches_signal_level() -> None:
    graph, src, dst = _linked_graph()
    signal = Signal(
        name="clk",
        signal_type=SignalType.CLOCK,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    trace = derive_trace_from_signal(signal)
    assert level_from_value(signal.value) == trace.samples[-1].level
    assert trace.level_at(trace.end_time) == LogicLevel.HIGH


def test_bundle_clock_and_data_traces() -> None:
    graph, src, dst = _linked_graph()
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    data.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    bundle = derive_bundle_from_signals((clock, data))
    assert len(bundle.traces) == 2
    assert bundle.trace_named("clk") is not None
    assert bundle.trace_named("data") is not None


def test_timing_events_from_propagation_rising_edge() -> None:
    graph, src, dst = _linked_graph()
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(src.get_pin("out"), dst.get_pin("in"), graph=graph)
    events = timing_events_from_propagation(signal)
    assert len(events) == 1
    assert events[0].edge == TimingEdge.RISING
    assert events[0].pin_id == "dst.in"
