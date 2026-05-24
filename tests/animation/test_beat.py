"""play_propagation_beat parallel orchestration."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup

from manim_engineering.animation import BEAT_DURATION, play_propagation_beat
from manim_engineering.animation.signal_flow import SignalFlow
from manim_engineering.animation.waveform_sync import WaveformSync
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals


def _clock_data_fixture():
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
    bundle = derive_bundle_from_signals((clock, data))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return graph, layout, clock, data, bundle, panel_spec


class _RecordingScene:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.played: list[tuple[object, ...]] = []
        self.run_times: list[float | None] = []
        self.removed: list[object] = []

    def add(self, *mobjects: object) -> None:
        self.added.extend(mobjects)

    def play(self, *animations: object, run_time: float | None = None) -> None:
        self.played.append(animations)
        self.run_times.append(run_time)

    def remove(self, *mobjects: object) -> None:
        self.removed.extend(mobjects)


def test_beat_single_play_with_parallel_run_time() -> None:
    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    scene = _RecordingScene()
    used = play_propagation_beat(
        scene,
        clock,
        layout=layout,
        graph=graph,
        duration=BEAT_DURATION,
        bundle=bundle,
        signals=(clock, data),
        panel_spec=panel_spec,
        beat=0,
    )
    assert used == pytest.approx(BEAT_DURATION)
    assert len(scene.played) == 2
    assert scene.run_times[0] == pytest.approx(BEAT_DURATION)
    root = scene.played[0][0]
    assert isinstance(root, AnimationGroup)
    assert scene.removed


def test_waveform_sync_aligns_with_signal_flow_duration() -> None:
    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    flow = SignalFlow(clock, layout=layout, graph=graph, duration=BEAT_DURATION)
    sync = WaveformSync(
        bundle,
        (clock, data),
        panel_spec=panel_spec,
        duration=BEAT_DURATION,
    )
    assert sync.aligns_with_signal_flow(flow.duration)


def test_reveal_only_beat_uses_full_duration_when_no_flow_anims() -> None:
    from unittest.mock import patch

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()

    class _Line:
        class _Anim:
            def set_stroke(self, **_kwargs: object) -> str:
                return "anim"

        animate = _Anim()

    class _RevealTracker:
        def append_through_time(self, _reveal_time: float) -> list[_Line]:
            return [_Line()]

    empty_flow = AnimationPlan(
        overlays=(),
        propagation_overlays=(),
        animations=(),
        run_time=BEAT_DURATION,
    )
    scene = _RecordingScene()
    with patch.object(SignalFlow, "build", return_value=empty_flow):
        used = play_propagation_beat(
            scene,
            clock,
            layout=layout,
            graph=graph,
            duration=BEAT_DURATION,
            reveal_tracker=_RevealTracker(),
            reveal_time=0.0,
        )
    assert used == pytest.approx(BEAT_DURATION)
    assert len(scene.played) == 1
    assert scene.run_times[0] == pytest.approx(BEAT_DURATION)
