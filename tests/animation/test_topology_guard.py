"""Animation must not mutate circuit topology."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def test_signal_flow_build_does_not_change_topology() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    conn_before = tuple(c.id for c in graph.connections)
    node_before = tuple(n.id for n in graph.nodes)

    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)

    SignalFlow(signal, layout=layout, graph=graph).build()

    assert tuple(c.id for c in graph.connections) == conn_before
    assert tuple(n.id for n in graph.nodes) == node_before
    assert len(graph.connections) == 1
