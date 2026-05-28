"""play_propagation_beat parallel orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("manim")

from recording_scene import RecordingScene
from scene_trace import trace_stage_names

from manim_engineering.animation import BEAT_DURATION, TeachingStyle, play_propagation_beat
from manim_engineering.animation.beat import _phase_durations
from manim_engineering.animation.signal_flow import SignalFlow
from manim_engineering.animation.trace import flush_trace, reset_tracer
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
    assert len(scene.played) == 3
    assert len(scene.waited) == 1
    assert 0.0 < scene.run_times[0] < BEAT_DURATION
    assert 0.0 < scene.run_times[1] < BEAT_DURATION
    assert 0.0 < scene.waited[0] < BEAT_DURATION
    assert scene.run_times[0] + scene.waited[0] + scene.run_times[1] == pytest.approx(BEAT_DURATION)
    root = scene.played[0][0]
    assert root.__class__.__name__ in {"ShowPassingFlash", "AnimationGroup"}
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

    import numpy as np
    from manim import Line, VGroup

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow
    from manim_engineering.animation.waveform_reveal import SegmentRevealPlan
    from manim_engineering.renderers.minimal.labels import prepare_stroke_reveal

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()

    def _create_line() -> Line:
        line = Line(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        prepare_stroke_reveal((line,))
        return line

    class _RevealTracker:
        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, _reveal_time: float) -> tuple[SegmentRevealPlan, ...]:
            return (SegmentRevealPlan(trace_group=VGroup(), added=(_create_line(),)),)

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


def test_reveal_only_beat_restores_line_opacity_after_play() -> None:
    from unittest.mock import patch

    import numpy as np
    from manim import Line, VGroup

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow
    from manim_engineering.animation.waveform_reveal import SegmentRevealPlan
    from manim_engineering.renderers.minimal.labels import prepare_stroke_reveal

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()

    def _create_line() -> Line:
        line = Line(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        prepare_stroke_reveal((line,))
        return line

    class _RevealTracker:
        def __init__(self) -> None:
            self.last_lines: list[Line] = []

        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, _reveal_time: float) -> tuple[SegmentRevealPlan, ...]:
            line = _create_line()
            self.last_lines = [line]
            return (SegmentRevealPlan(trace_group=VGroup(), added=(line,)),)

    empty_flow = AnimationPlan(
        overlays=(),
        propagation_overlays=(),
        animations=(),
        run_time=BEAT_DURATION,
    )
    tracker = _RevealTracker()
    scene = RecordingScene()
    with patch.object(SignalFlow, "build", return_value=empty_flow):
        play_propagation_beat(
            scene,
            clock,
            layout=layout,
            graph=graph,
            duration=BEAT_DURATION,
            reveal_tracker=tracker,
            reveal_time=0.0,
        )
    assert tracker.last_lines
    assert float(tracker.last_lines[0].get_stroke_opacity()) == pytest.approx(1.0)


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
    tracker.sync_idle_baselines()
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
    # Fresh reveal geometry now owns the beat; no extra timing flash overlay stacks on top.
    assert len(scene.played) == 1
    assert scene.run_times[0] == pytest.approx(BEAT_DURATION)
    assert scene.played[0][0].__class__.__name__ != "ShowPassingFlash"


def test_reveal_and_flow_run_as_two_ordered_subphases() -> None:
    from manim_engineering.animation.waveform_reveal import WaveformRevealTracker

    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    panel_renderer = WaveformPanelRenderer()
    panel, _ = panel_renderer.render_with_layout(bundle, layout, idle_only=True)
    tracker = WaveformRevealTracker(panel, bundle, panel_spec, panel_renderer)
    tracker.sync_idle_baselines()
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
    )
    assert used == pytest.approx(BEAT_DURATION)
    assert len(scene.played) == 3
    assert len(scene.waited) == 1
    assert scene.run_times[0] < BEAT_DURATION
    assert scene.run_times[1] < BEAT_DURATION
    assert 0.0 < scene.waited[0] < BEAT_DURATION
    assert scene.run_times[0] + scene.waited[0] + scene.run_times[1] == pytest.approx(BEAT_DURATION)


def test_analog_reveal_uses_single_commit_path() -> None:
    from unittest.mock import patch

    import numpy as np
    from manim import Line, VGroup

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow
    from manim_engineering.animation.waveform_reveal import SegmentRevealPlan
    from manim_engineering.renderers.minimal.labels import prepare_stroke_reveal

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()

    def _create_line(start_xy: tuple[float, float], end_xy: tuple[float, float]) -> Line:
        line = Line(
            np.array([start_xy[0], start_xy[1], 0.0]),
            np.array([end_xy[0], end_xy[1], 0.0]),
        )
        prepare_stroke_reveal((line,))
        return line

    class _RevealTracker:
        def __init__(self) -> None:
            self.last_lines: list[Line] = []

        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time_for(
            self,
            _signal_name: str,
            _reveal_time: float,
        ) -> SegmentRevealPlan:
            lines = [
                _create_line((0.0, 0.0), (0.5, 0.2)),
                _create_line((0.5, 0.2), (1.0, 0.35)),
                _create_line((1.0, 0.35), (1.5, 0.5)),
            ]
            self.last_lines = lines
            return SegmentRevealPlan(trace_group=VGroup(), added=tuple(lines))

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
            reveal_time=1.0,
            reveal_scope="signal",
            wire_pulse=False,
        )
    assert len(scene.played) == 1
    assert scene.played[0][0].__class__.__name__ == "Create"
    assert tracker.last_lines
    assert float(tracker.last_lines[-1].get_stroke_opacity()) == pytest.approx(1.0)


def test_reveal_scope_signal_uses_single_trace_append() -> None:
    from unittest.mock import patch

    import numpy as np
    from manim import Line, VGroup

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow
    from manim_engineering.animation.waveform_reveal import SegmentRevealPlan
    from manim_engineering.renderers.minimal.labels import prepare_stroke_reveal

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()

    def _create_line() -> Line:
        line = Line(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        prepare_stroke_reveal((line,))
        return line

    class _RevealTracker:
        def __init__(self) -> None:
            self.all_calls: list[float] = []
            self.signal_calls: list[tuple[str, float]] = []

        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, reveal_time: float) -> SegmentRevealPlan:
            self.all_calls.append(reveal_time)
            return SegmentRevealPlan(trace_group=VGroup(), added=(_create_line(),))

        def append_through_time_for(
            self,
            signal_name: str,
            reveal_time: float,
        ) -> SegmentRevealPlan:
            self.signal_calls.append((signal_name, reveal_time))
            return SegmentRevealPlan(trace_group=VGroup(), added=(_create_line(),))

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


def test_teaching_style_overrides_beat_duration() -> None:
    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    scene = RecordingScene()
    custom_duration = 2.5
    style = TeachingStyle(beat_duration=custom_duration)
    used = play_propagation_beat(
        scene,
        clock,
        layout=layout,
        graph=graph,
        bundle=bundle,
        signals=(clock, data),
        panel_spec=panel_spec,
        beat=0,
        style=style,
    )
    assert used == pytest.approx(custom_duration)
    assert len(scene.waited) == 1
    assert (
        scene.run_times[0] + scene.waited[0] + scene.run_times[1]
        == pytest.approx(custom_duration)
    )


def test_default_teaching_style_matches_beat_duration_constant() -> None:
    assert TeachingStyle().beat_duration == pytest.approx(BEAT_DURATION)


def test_commit_settle_duration_scales_with_commit_shape() -> None:
    sparse = _phase_durations(
        BEAT_DURATION,
        has_waveform_commit=True,
        has_timing_accent=False,
        has_playback=True,
        commit_line_count=1,
        commit_overlay_count=0,
    )
    dense = _phase_durations(
        BEAT_DURATION,
        has_waveform_commit=True,
        has_timing_accent=False,
        has_playback=True,
        commit_line_count=4,
        commit_overlay_count=1,
    )
    assert dense.commit_settle > sparse.commit_settle
    assert (
        dense.waveform_commit + dense.commit_settle + dense.playback
        == pytest.approx(BEAT_DURATION)
    )


def test_waveform_commit_stage_recorded_when_reveal_adds_lines(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from unittest.mock import patch

    import numpy as np
    from manim import Line, VGroup

    from manim_engineering.animation.base import AnimationPlan
    from manim_engineering.animation.signal_flow import SignalFlow
    from manim_engineering.animation.waveform_reveal import SegmentRevealPlan
    from manim_engineering.renderers.minimal.labels import prepare_stroke_reveal

    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()

    def _create_line() -> Line:
        line = Line(np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]))
        prepare_stroke_reveal((line,))
        return line

    class _RevealTracker:
        def revealed_time_for(self, _signal_name: str) -> float:
            return 0.0

        def append_through_time(self, _reveal_time: float) -> tuple[SegmentRevealPlan, ...]:
            return (SegmentRevealPlan(trace_group=VGroup(), added=(_create_line(),)),)

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
            reveal_tracker=_RevealTracker(),
            reveal_time=0.0,
        )
    path = flush_trace(scene)
    assert path is not None
    assert trace_stage_names(path) == ["beat.waveform_commit", "beat.play"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    commit_entry, play_entry = payload["stages"]
    assert commit_entry["run_time"] == pytest.approx(BEAT_DURATION)
    assert play_entry["run_time"] == 0.0


def test_waveform_commit_stage_omitted_without_new_reveal(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph, layout, clock, _data, _bundle, _panel_spec = _clock_data_fixture()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    scene = RecordingScene()
    play_propagation_beat(
        scene,
        clock,
        layout=layout,
        graph=graph,
        duration=BEAT_DURATION,
        wire_pulse=False,
    )
    path = flush_trace(scene)
    assert path is not None
    assert trace_stage_names(path) == ["beat.play"]


def test_timing_accent_stage_recorded_for_waveform_sync(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    scene = RecordingScene()
    play_propagation_beat(
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
    path = flush_trace(scene)
    assert path is not None
    assert trace_stage_names(path) == ["beat.timing_accent", "beat.timing_settle", "beat.play"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    accent_entry, settle_entry, play_entry = payload["stages"]
    assert accent_entry["detail"]["from_pin_id"] == clock.propagation_history[0].from_pin_id
    assert accent_entry["detail"]["to_pin_id"] == clock.propagation_history[0].to_pin_id
    assert accent_entry["detail"]["timing_mode"] == "auto"
    assert 0.0 < accent_entry["run_time"] < BEAT_DURATION
    assert 0.0 < settle_entry["run_time"] < BEAT_DURATION
    assert 0.0 < play_entry["run_time"] < BEAT_DURATION
    assert (
        accent_entry["run_time"]
        + settle_entry["run_time"]
        + play_entry["run_time"]
        == pytest.approx(BEAT_DURATION)
    )


def test_timing_accent_stage_omitted_when_reveal_commit_owns_beat(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from manim_engineering.animation.waveform_reveal import WaveformRevealTracker

    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    panel_renderer = WaveformPanelRenderer()
    panel, _ = panel_renderer.render_with_layout(bundle, layout, idle_only=True)
    tracker = WaveformRevealTracker(panel, bundle, panel_spec, panel_renderer)
    tracker.sync_idle_baselines()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    scene = RecordingScene()
    play_propagation_beat(
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
    path = flush_trace(scene)
    assert path is not None
    assert trace_stage_names(path) == ["beat.waveform_commit", "beat.play"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    commit_entry, play_entry = payload["stages"]
    assert commit_entry["detail"]["from_pin_id"] == clock.propagation_history[0].from_pin_id
    assert commit_entry["detail"]["to_pin_id"] == clock.propagation_history[0].to_pin_id
    assert commit_entry["detail"]["reveal_target_count"] == 1
    assert commit_entry["detail"]["reveal_signal_names"] == ["clk"]
    assert play_entry["detail"]["timing_purpose"] is None


def test_reveal_and_flow_trace_use_split_subphase_durations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from manim_engineering.animation.waveform_reveal import WaveformRevealTracker

    graph, layout, clock, data, bundle, panel_spec = _clock_data_fixture()
    panel_renderer = WaveformPanelRenderer()
    panel, _ = panel_renderer.render_with_layout(bundle, layout, idle_only=True)
    tracker = WaveformRevealTracker(panel, bundle, panel_spec, panel_renderer)
    tracker.sync_idle_baselines()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    scene = RecordingScene()
    play_propagation_beat(
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
    )
    path = flush_trace(scene)
    assert path is not None
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert trace_stage_names(path) == ["beat.waveform_commit", "beat.commit_settle", "beat.play"]
    commit_entry, settle_entry, play_entry = payload["stages"]
    assert 0.0 < commit_entry["run_time"] < BEAT_DURATION
    assert 0.0 < settle_entry["run_time"] < BEAT_DURATION
    assert 0.0 < play_entry["run_time"] < BEAT_DURATION
    assert settle_entry["run_time"] == pytest.approx(_phase_durations(
        BEAT_DURATION,
        has_waveform_commit=True,
        has_timing_accent=False,
        has_playback=True,
        commit_line_count=settle_entry["detail"]["line_count"],
        commit_overlay_count=settle_entry["detail"]["overlay_count"],
    ).commit_settle)
    assert (
        commit_entry["run_time"]
        + settle_entry["run_time"]
        + play_entry["run_time"]
        == pytest.approx(BEAT_DURATION)
    )
