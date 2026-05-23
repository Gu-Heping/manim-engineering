"""WaveformSync contract: timing purpose and SignalFlow alignment."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.animation import (
    DEFAULT_PROPAGATION_DURATION,
    AnimationPurpose,
    SignalFlow,
    WaveformSync,
)
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals, panel_below_layout


def _clock_data_fixture() -> tuple[CircuitGraph, dict[str, Resistor], object, Signal, Signal]:
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    drv.attach_to(graph)
    rcv.attach_to(graph)
    graph.connect(drv.get_pin("b"), rcv.get_pin("a"))
    graph.connect(drv.get_pin("a"), rcv.get_pin("b"))
    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().layout(graph, elements)
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.get_pin("b"), rcv.get_pin("a"), graph=graph)
    data.propagate(drv.get_pin("a"), rcv.get_pin("b"), graph=graph)
    return graph, elements, layout, clock, data


def test_waveform_sync_purpose_is_timing() -> None:
    assert WaveformSync.purpose == AnimationPurpose.TIMING


def test_waveform_sync_aligns_duration_with_signal_flow() -> None:
    _, _, layout, clock, data = _clock_data_fixture()
    bundle = derive_bundle_from_signals((clock, data))
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    sync = WaveformSync(bundle, (clock, data), panel_spec=panel)
    flow = SignalFlow(clock, layout=layout)
    assert sync.aligns_with_signal_flow(flow.duration)
    assert sync.duration == DEFAULT_PROPAGATION_DURATION


def test_waveform_sync_build_does_not_mutate_topology() -> None:
    graph, elements, layout, clock, data = _clock_data_fixture()
    conn_before = tuple(c.id for c in graph.connections)
    bundle = derive_bundle_from_signals((clock, data))
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    WaveformSync(bundle, (clock, data), panel_spec=panel).build()
    assert tuple(c.id for c in graph.connections) == conn_before


def test_waveform_sync_resolved_beat_matches_history() -> None:
    _, _, layout, clock, data = _clock_data_fixture()
    bundle = derive_bundle_from_signals((clock, data))
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    sync = WaveformSync(bundle, (clock, data), panel_spec=panel)
    assert sync.resolved_beat() == len(clock.propagation_history) - 1


class _RecordingScene:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.played: list[tuple[object, ...]] = []

    def add(self, *mobjects: object) -> None:
        self.added.extend(mobjects)

    def play(self, *animations: object, run_time: float | None = None) -> None:
        self.played.append(animations)


def test_waveform_sync_play_adds_markers() -> None:
    _, _, layout, clock, data = _clock_data_fixture()
    bundle = derive_bundle_from_signals((clock, data))
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    scene = _RecordingScene()
    WaveformSync(bundle, (clock, data), panel_spec=panel, duration=0.8).play(scene)
    assert len(scene.added) >= 1
    assert len(scene.played) == 1
