"""Explicit level application for protocol bit sequences."""

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
    apply_level_between_pins,
)


def test_apply_level_arbitrary_sequence() -> None:
    graph = CircuitGraph()
    src = Node(id="src")
    dst = Node(id="dst")
    src.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DATA)
    dst.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DATA)
    graph.add_node(src)
    graph.add_node(dst)
    graph.connect(src.get_pin("out"), dst.get_pin("in"))

    signal = Signal(
        name="data",
        signal_type=SignalType.DATA,
        value=LogicState(level=LogicLevel.HIGH),
    )
    apply_level_between_pins(
        signal,
        src.get_pin("out"),
        dst.get_pin("in"),
        LogicLevel.LOW,
        graph=graph,
    )
    apply_level_between_pins(
        signal,
        src.get_pin("out"),
        dst.get_pin("in"),
        LogicLevel.HIGH,
        graph=graph,
    )
    levels = [r.new_value.level for r in signal.propagation_history if r.new_value is not None]
    assert levels == [LogicLevel.LOW, LogicLevel.HIGH]
