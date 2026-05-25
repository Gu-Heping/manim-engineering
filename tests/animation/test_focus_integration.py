"""Focus dim/restore integration with real topology projection."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from conftest import RecordingScene

from manim_engineering.animation import BEAT_DURATION, play_propagation_beat
from manim_engineering.animation.focus import DEFAULT_DIM_OPACITY, dim_topology, restore_topology
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.renderers.minimal.labels import iter_label_roots, iter_symbol_strokes
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _topology_projection():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return layout, graph, signal, topology


def test_dim_restore_round_trip_on_rendered_topology() -> None:
    _layout, _graph, _signal, topology = _topology_projection()
    dim_topology(topology)
    for stroke in iter_symbol_strokes(topology.components):
        assert stroke.get_stroke_opacity() == pytest.approx(DEFAULT_DIM_OPACITY)
    for label in iter_label_roots(topology.components):
        label_opacity = label.get_opacity()
        if label_opacity is None:
            label_opacity = label.get_fill_opacity()
        assert label_opacity == pytest.approx(DEFAULT_DIM_OPACITY)
    restore_topology(topology)
    for stroke in iter_symbol_strokes(topology.components):
        assert stroke.get_stroke_opacity() == pytest.approx(1.0)
    for label in iter_label_roots(topology.components):
        label_opacity = label.get_opacity()
        if label_opacity is None:
            label_opacity = label.get_fill_opacity()
        assert label_opacity == pytest.approx(1.0)


def test_dim_then_beat_then_restore_preserves_label_contrast() -> None:
    layout, graph, signal, topology = _topology_projection()
    dim_topology(topology)
    scene = RecordingScene()
    play_propagation_beat(
        scene,
        signal,
        layout=layout,
        graph=graph,
        record=signal.propagation_history[0],
        duration=BEAT_DURATION,
        wire_pulse=True,
    )
    restore_topology(topology)
    for stroke in iter_symbol_strokes(topology.components):
        assert stroke.get_stroke_opacity() == pytest.approx(1.0)
