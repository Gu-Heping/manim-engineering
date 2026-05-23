"""Rendered topology must stay immutable across SignalFlow.build()."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Line

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _line_points_snapshot(lines: tuple[Line, ...]) -> list[np.ndarray]:
    return [np.array(line.get_all_points(), dtype=float).copy() for line in lines]


def _collect_lines(group) -> tuple[Line, ...]:
    lines: list[Line] = []

    def walk(node) -> None:
        if isinstance(node, Line):
            lines.append(node)
            return
        for sub in getattr(node, "submobjects", ()):
            walk(sub)

    walk(group)
    return tuple(lines)


def _component_submobject_counts(components) -> list[int]:
    return [len(comp.submobjects) for comp in components.submobjects]


def test_signal_flow_build_preserves_topology_projection() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)

    wire_lines = _collect_lines(topology.wires)
    assert wire_lines
    wires_before = _line_points_snapshot(wire_lines)
    counts_before = _component_submobject_counts(topology.components)

    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    SignalFlow(signal, layout=layout, graph=graph).build()

    wires_after = _line_points_snapshot(wire_lines)
    counts_after = _component_submobject_counts(topology.components)

    assert counts_before == counts_after
    for pts_before, pts_after in zip(wires_before, wires_after, strict=True):
        np.testing.assert_array_equal(pts_before, pts_after)
