"""SignalFlow must not mutate rendered wire Line geometry."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Line

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType


def _line_points_snapshot(lines: tuple[Line, ...]) -> list[np.ndarray]:
    return [np.array(line.get_all_points(), dtype=float).copy() for line in lines]


def _wire_lines_from_circuit(circuit) -> tuple[Line, ...]:
    from manim import Line as LineType

    lines: list[Line] = []

    def walk(node) -> None:
        if isinstance(node, LineType):
            lines.append(node)
            return
        for sub in getattr(node, "submobjects", ()):
            walk(sub)

    walk(circuit)
    return tuple(lines)


def test_signal_flow_build_does_not_mutate_wire_lines() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    circuit = MinimalRenderer().render_layout(layout, graph, elements)
    wire_lines = _wire_lines_from_circuit(circuit)
    assert wire_lines

    before = _line_points_snapshot(wire_lines)
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    SignalFlow(signal, layout=layout, graph=graph, wire_mobjects=wire_lines).build()
    after = _line_points_snapshot(wire_lines)

    assert len(before) == len(after)
    for pts_before, pts_after in zip(before, after, strict=True):
        np.testing.assert_array_equal(pts_before, pts_after)
