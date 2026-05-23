"""WaveformSync uses detached segment overlays."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import ShowPassingFlash

from manim_engineering.animation import WaveformSync
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals


def _fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((clock,))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return layout, clock, bundle, panel_spec


def test_waveform_sync_builds_flash_overlays() -> None:
    layout, clock, bundle, panel_spec = _fixture()
    plan = WaveformSync(bundle, (clock,), panel_spec=panel_spec).build()
    assert len(plan.propagation_overlays) >= 1
    assert len(plan.animations) == 1
    root = plan.animations[0]
    if hasattr(root, "animations"):
        assert any(isinstance(a, ShowPassingFlash) for a in root.animations)
    else:
        assert isinstance(root, ShowPassingFlash)


def test_waveform_sync_active_signal_isolates_one_trace() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clk.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    data.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((clk, data))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    plan = WaveformSync(
        bundle,
        (clk, data),
        panel_spec=panel_spec,
        beat=0,
        active_signal=clk,
    ).build()
    assert len(plan.propagation_overlays) == 1
