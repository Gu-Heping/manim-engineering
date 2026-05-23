"""SignalFlow must not mutate rendered wire Line geometry."""

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


def test_signal_flow_build_does_not_mutate_wire_lines() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)
    wire_lines = topology.wire_lines()
    assert wire_lines

    before = _line_points_snapshot(wire_lines)
    component_counts_before = [len(c.submobjects) for c in topology.components.submobjects]
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    plan = SignalFlow(signal, layout=layout, graph=graph, wire_mobjects=wire_lines).build()
    after = _line_points_snapshot(wire_lines)
    component_counts_after = [len(c.submobjects) for c in topology.components.submobjects]
    assert component_counts_before == component_counts_after
    path = plan.propagation_overlays[0]
    assert id(path) not in {id(line) for line in wire_lines}
    wire_flash_targets = plan.propagation_overlays[-len(wire_lines) :]
    for target, source in zip(wire_flash_targets, wire_lines, strict=True):
        assert id(target) != id(source)

    assert len(before) == len(after)
    for pts_before, pts_after in zip(before, after, strict=True):
        np.testing.assert_array_equal(pts_before, pts_after)
