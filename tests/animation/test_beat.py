"""play_propagation_beat parallel orchestration."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup
from conftest import RecordingScene

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


def test_play_propagation_beat_rejects_scene_without_play() -> None:
    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()
    with pytest.raises(TypeError, match="play\\(\\)"):
        play_propagation_beat(object(), clock, layout=layout, graph=graph)


def test_beat_single_play_with_parallel_run_time() -> None:
    from manim_engineering.animation.layers import PROPAGATION_Z_INDEX

    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    scene = RecordingScene()
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
    propagation_groups = [mob for mob in scene.added if hasattr(mob, "get_z_index")]
    assert any(mob.get_z_index() == PROPAGATION_Z_INDEX for mob in propagation_groups)
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
        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, _reveal_time: float) -> list[_Line]:
            return [_Line()]

    empty_flow = AnimationPlan(
        overlays=(),
        propagation_overlays=(),
        animations=(),
        run_time=BEAT_DURATION,
    )
    scene = RecordingScene()
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


def test_wire_pulse_false_skips_signal_flow_animations() -> None:
    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    scene = RecordingScene()
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
        wire_pulse=False,
    )
    assert used == pytest.approx(BEAT_DURATION)
    assert len(scene.played) == 2
    assert scene.played[0][0].__class__.__name__ == "ShowPassingFlash"


def test_reveal_and_flow_share_single_beat_play() -> None:
    from manim_engineering.animation.waveform_reveal import WaveformRevealTracker

    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    panel_renderer = WaveformPanelRenderer()
    panel, _ = panel_renderer.render_with_layout(bundle, layout, idle_only=True)
    tracker = WaveformRevealTracker(panel, bundle, panel_spec, panel_renderer)
    scene = RecordingScene()
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
        reveal_tracker=tracker,
        reveal_targets=((clock, 0),),
        wire_pulse=False,
    )
    assert used == pytest.approx(BEAT_DURATION)
    # One beat play (reveal + timing together) plus overlay fade-out removal.
    assert len(scene.played) == 2
    assert scene.run_times[0] == pytest.approx(BEAT_DURATION)


def test_reveal_scope_signal_uses_single_trace_append() -> None:
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
        all_calls: list[float] = []
        signal_calls: list[tuple[str, float]] = []

        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, reveal_time: float) -> list[_Line]:
            self.all_calls.append(reveal_time)
            return [_Line()]

        def append_through_time_for(self, signal_name: str, reveal_time: float) -> list[_Line]:
            self.signal_calls.append((signal_name, reveal_time))
            return [_Line()]

    tracker = _RevealTracker()
    empty_flow = AnimationPlan(
        overlays=(),
        propagation_overlays=(),
        animations=(),
        run_time=BEAT_DURATION,
    )
    scene = RecordingScene()
    with patch.object(SignalFlow, "build", return_value=empty_flow):
        play_propagation_beat(
            scene,
            clock,
            layout=layout,
            graph=graph,
            duration=BEAT_DURATION,
            reveal_tracker=tracker,
            reveal_time=2.0,
            reveal_scope="signal",
            wire_pulse=False,
        )
    assert tracker.signal_calls == [("clk", 2.0)]
    assert tracker.all_calls == []


def test_empty_beat_anims_waits_for_duration() -> None:
    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()
    scene = RecordingScene()
    used = play_propagation_beat(
        scene,
        clock,
        layout=layout,
        graph=graph,
        duration=BEAT_DURATION,
        wire_pulse=False,
    )
    assert used == pytest.approx(BEAT_DURATION)
    assert len(scene.waited) == 1
    assert scene.waited[0] == pytest.approx(BEAT_DURATION)
    assert len(scene.played) == 0
