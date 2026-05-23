"""Propagation overlays must not alias renderer wire topology."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _propagated_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return graph, elements, layout, signal


def test_propagation_path_is_not_wire_line_instance() -> None:
    graph, elements, layout, signal = _propagated_fixture()
    topology = ManimRenderer().render_topology(graph, layout, elements)
    wire_ids = {id(line) for line in topology.wire_lines()}
    plan = SignalFlow(signal, layout=layout, graph=graph).build()
    path = plan.propagation_overlays[0]
    assert id(path) not in wire_ids


def test_wire_flash_targets_are_copies_when_wire_mobjects_passed() -> None:
    graph, elements, layout, signal = _propagated_fixture()
    topology = ManimRenderer().render_topology(graph, layout, elements)
    wire_lines = topology.wire_lines()
    plan = SignalFlow(
        signal,
        layout=layout,
        graph=graph,
        wire_mobjects=wire_lines,
    ).build()
    assert len(plan.propagation_overlays) >= 2
    wire_flash_targets = plan.propagation_overlays[-len(wire_lines) :]
    for target, source in zip(wire_flash_targets, wire_lines, strict=True):
        assert id(target) != id(source)
