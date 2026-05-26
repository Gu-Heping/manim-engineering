"""PropagationSequence multi-beat playback."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup
from recording_scene import RecordingScene

from manim_engineering.animation import (
    BEAT_DURATION,
    BEAT_GAP,
    BeatAnimationError,
    BeatSpec,
    PropagationSequence,
)
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals


def _three_beat_signal_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    for _ in range(3):
        signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
        signal.value = LogicState(
            level=LogicLevel.HIGH if signal.value.level == LogicLevel.LOW else LogicLevel.LOW
        )
    return graph, layout, signal


def test_sequence_plays_one_wait_per_gap() -> None:
    graph, layout, signal = _three_beat_signal_fixture()

    waits: list[float] = []
    plays = 0

    class Scene:
        def wait(self, duration: float) -> None:
            waits.append(duration)

    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=3)

    def fake_beat(scene, sig, **kwargs):
        nonlocal plays
        plays += 1

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        seq.play(Scene())
    finally:
        ps_mod.play_propagation_beat = original

    assert plays == 3
    assert len(waits) == 2
    assert all(w == pytest.approx(BEAT_GAP) for w in waits)


def test_sequence_real_link_runs_each_beat_at_beat_duration() -> None:
    """No mocks: every beat must call ``scene.play(... run_time=BEAT_DURATION)``."""
    graph, layout, signal = _three_beat_signal_fixture()
    scene = RecordingScene()

    seq = PropagationSequence(
        signal,
        layout=layout,
        graph=graph,
        max_beats=3,
        beat_duration=BEAT_DURATION,
    )
    seq.play(scene)

    assert seq.beat_count == 3
    beat_plays = [
        rt for rt in scene.run_times if rt is not None and rt == pytest.approx(BEAT_DURATION)
    ]
    assert len(beat_plays) == 3
    assert len(scene.waited) == 2


def test_sequence_with_heterogeneous_beats_invokes_caption_callback() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    bundle = derive_bundle_from_signals((signal,))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)

    beats = tuple(
        BeatSpec(signal=signal, record=record, wave_beat=i, caption=f"beat {i}")
        for i, record in enumerate(signal.propagation_history[:3])
    )
    captions_seen: list[tuple[int, str | None]] = []

    def on_caption(spec: BeatSpec, index: int) -> None:
        captions_seen.append((index, spec.caption))

    scene = RecordingScene()
    seq = PropagationSequence(
        layout=layout,
        graph=graph,
        beats=beats,
        bundle=bundle,
        sync_signals=(signal,),
        panel_spec=panel_spec,
        caption_callback=on_caption,
    )
    seq.play(scene)

    assert captions_seen == [(0, "beat 0"), (1, "beat 1"), (2, "beat 2")]
    beat_plays = [
        animations
        for animations, rt in zip(scene.played, scene.run_times, strict=True)
        if rt is not None and rt == pytest.approx(BEAT_DURATION)
    ]
    assert len(beat_plays) == 3
    for animations in beat_plays:
        assert any(isinstance(a, AnimationGroup) or hasattr(a, "run_time") for a in animations)


def test_sequence_with_captions_holds_for_reading_before_each_beat() -> None:
    """Each beat with a caption must ``wait(BEAT_CAPTION_HOLD)`` between caption and motion."""
    from manim_engineering.animation import BEAT_CAPTION_HOLD

    graph, layout, signal = _three_beat_signal_fixture()
    bundle = derive_bundle_from_signals((signal,))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)

    beats = tuple(
        BeatSpec(signal=signal, record=record, wave_beat=i, caption=f"b{i}")
        for i, record in enumerate(signal.propagation_history[:3])
    )
    scene = RecordingScene()
    PropagationSequence(
        layout=layout,
        graph=graph,
        beats=beats,
        bundle=bundle,
        sync_signals=(signal,),
        panel_spec=panel_spec,
        caption_callback=lambda _spec, _i: None,
    ).play(scene)

    hold_count = sum(1 for w in scene.waited if w == pytest.approx(BEAT_CAPTION_HOLD))
    assert hold_count == 3, (
        f"expected 3 reading holds (one per captioned beat), got waits={scene.waited}"
    )


def test_sequence_waveform_reveal_runs_during_propagation_beat() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    events: list[str] = []

    class Scene:
        def wait(self, duration: float) -> None:
            pass

    class Tracker:
        def append_through_beat(self, sig, target: int) -> tuple[()]:
            return ()

    def fake_beat(scene, sig, **kwargs):
        tracker = kwargs.get("reveal_tracker")
        targets = kwargs.get("reveal_targets") or ()
        if tracker is not None and targets:
            for reveal_signal, target in targets:
                tracker.append_through_beat(reveal_signal, target)
            events.append("reveal")
        events.append("beat")

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        PropagationSequence(
            signal,
            layout=layout,
            graph=graph,
            max_beats=3,
            reveal_tracker=Tracker(),
        ).play(Scene())
    finally:
        ps_mod.play_propagation_beat = original

    assert events == ["reveal", "beat", "reveal", "beat", "reveal", "beat"]


def test_sequence_dim_inactive_requires_topology() -> None:
    """``dim_inactive=True`` without ``topology=`` previously no-op'd silently."""
    graph, layout, signal = _three_beat_signal_fixture()
    with pytest.raises(ValueError, match="topology"):
        PropagationSequence(
            signal,
            layout=layout,
            graph=graph,
            max_beats=3,
            dim_inactive=True,
        )


def test_sequence_wraps_beat_failure_as_beat_animation_error() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    calls = 0

    class Scene:
        def wait(self, duration: float) -> None:
            pass

    def failing_beat(scene, sig, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("boom")

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = failing_beat
    try:
        with pytest.raises(BeatAnimationError) as exc_info:
            PropagationSequence(signal, layout=layout, graph=graph, max_beats=3).play(Scene())
    finally:
        ps_mod.play_propagation_beat = original

    err = exc_info.value
    assert err.beat_index == 1
    assert err.signal_name == "edge"
    assert err.stage == "beat.play"
    assert isinstance(err.cause, RuntimeError)


def test_sequence_snapshot_checkpoints_when_env_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    calls: list[str] = []

    def fake_snapshot(scene: object, label: str) -> None:
        calls.append(label)

    monkeypatch.setenv("ME_ANIMATION_SNAPSHOT", "1")
    import manim_engineering.debug.snapshot as snapshot_mod

    monkeypatch.setattr(snapshot_mod, "snapshot_frame", fake_snapshot)
    monkeypatch.setattr(snapshot_mod, "snapshot_topology", lambda _scene, _label: None)

    class Scene:
        def wait(self, duration: float) -> None:
            pass

    def noop_beat(scene, sig, **kwargs):
        pass

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = noop_beat
    try:
        PropagationSequence(signal, layout=layout, graph=graph, max_beats=2).play(Scene())
    finally:
        ps_mod.play_propagation_beat = original

    assert calls == ["beat_00_before", "beat_00_after", "beat_01_before", "beat_01_after"]
