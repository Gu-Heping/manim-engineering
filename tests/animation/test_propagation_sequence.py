"""PropagationSequence multi-beat playback."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, VGroup
from recording_scene import RecordingScene
from scene_trace import trace_stage_names

from manim_engineering.animation import (
    BEAT_CAPTION_HOLD,
    BEAT_DURATION,
    BEAT_GAP,
    BeatAnimationError,
    BeatSpec,
    PropagationSequence,
    TeachingStyle,
)
from manim_engineering.animation.trace import flush_trace, record_stage, reset_tracer
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    detach_label_roots,
    hide_labels,
    iter_label_roots,
    label_visible,
)
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals

REPO = Path(__file__).resolve().parents[2]


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


def _load_cmos_module():
    spec = importlib.util.spec_from_file_location(
        "cmos_inverter",
        REPO / "examples/analog/03_cmos_inverter.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    assert len(scene.played) >= 3
    assert sum(1 for rt in scene.run_times if rt is not None and rt > 0.0) >= 3
    for animations in scene.played[:3]:
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
        def append_through_beat(self, sig, target: int):
            from manim import VGroup

            from manim_engineering.animation.waveform_reveal import SegmentRevealPlan

            return SegmentRevealPlan(trace_group=VGroup())

    def fake_beat(scene, sig, **kwargs):
        controller = kwargs.get("waveform_controller")
        targets = kwargs.get("reveal_targets") or ()
        if controller is not None and targets:
            for reveal_signal, target in targets:
                controller.plan_reveal_for_beat(reveal_signal, target)
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


def test_sequence_resolves_context_emphasis_before_duration_override() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        emphasis="context",
    )
    resolved = seq._resolve_style(spec)
    assert resolved.beat_duration < BEAT_DURATION
    assert resolved.beat_gap < BEAT_GAP


def test_sequence_resolves_key_emphasis_from_custom_style() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    base = TeachingStyle(beat_duration=1.0, beat_gap=0.4, pulse_flash_width=0.5)
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1, style=base)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        emphasis="key",
    )
    resolved = seq._resolve_style(spec)
    assert resolved.beat_duration > base.beat_duration
    assert resolved.beat_gap > base.beat_gap
    assert resolved.pulse_flash_width > base.pulse_flash_width


def test_sequence_duration_override_wins_over_emphasis_duration() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        emphasis="key",
        duration=2.5,
    )
    resolved = seq._resolve_style(spec)
    assert resolved.beat_duration == pytest.approx(2.5)
    assert resolved.beat_gap > BEAT_GAP


def test_sequence_maps_context_emphasis_to_setup_profile() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        emphasis="context",
    )
    assert seq._resolve_transition_profile(spec) == "setup"


def test_sequence_maps_key_emphasis_to_conclusion_profile() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        emphasis="key",
    )
    assert seq._resolve_transition_profile(spec) == "conclusion"


def test_explicit_transition_profile_wins_over_emphasis_mapping() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="default",
        emphasis="key",
    )
    assert seq._resolve_transition_profile(spec) == "default"


def test_setup_profile_scales_caption_settle_and_adds_post_hold() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="setup",
        caption="setup beat",
    )
    resolved = seq._resolve_style(spec)
    assert seq._caption_settle_duration(spec, resolved) > BEAT_CAPTION_HOLD
    assert seq._post_beat_hold(spec, resolved) > 0.0


def test_longer_caption_adds_small_extra_settle() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    short = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="setup",
        caption="short",
    )
    long = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="setup",
        caption="this setup caption is intentionally longer",
    )
    style = seq._resolve_style(short)
    assert seq._caption_settle_duration(long, style) > seq._caption_settle_duration(short, style)


def test_conclusion_profile_holds_longer_than_setup() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    setup = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="setup",
        caption="setup beat",
    )
    conclusion = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="conclusion",
        caption="conclusion beat",
    )
    setup_style = seq._resolve_style(setup)
    conclusion_style = seq._resolve_style(conclusion)
    assert seq._caption_settle_duration(
        conclusion,
        conclusion_style,
    ) > seq._caption_settle_duration(setup, setup_style)
    assert seq._post_beat_hold(conclusion, conclusion_style) > seq._post_beat_hold(
        setup, setup_style
    )


def test_denser_post_hold_adds_small_extra_time() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    spec = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="conclusion",
        caption="short",
    )
    dense = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="conclusion",
        caption="this conclusion caption is intentionally longer",
    )
    style = seq._resolve_style(spec)
    assert seq._post_beat_hold(
        dense,
        style,
        caption_len=len(dense.caption or ""),
        reveal_target_count=3,
    ) > seq._post_beat_hold(
        spec,
        style,
        caption_len=len(spec.caption or ""),
        reveal_target_count=1,
    )


def test_conclusion_topology_focus_settle_accounts_for_endpoint_emphasis() -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    seq = PropagationSequence(signal, layout=layout, graph=graph, max_beats=1)
    setup = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="setup",
    )
    conclusion = BeatSpec(
        signal=signal,
        record=signal.propagation_history[0],
        transition_profile="conclusion",
    )
    setup_style = seq._resolve_style(setup)
    conclusion_style = seq._resolve_style(conclusion)
    assert seq._topology_focus_settle_duration(
        conclusion,
        conclusion_style,
        endpoint_emphasis=True,
        animation_count=2,
    ) > seq._topology_focus_settle_duration(
        setup,
        setup_style,
        endpoint_emphasis=False,
        animation_count=1,
    )


def test_sequence_reveals_phase_labels_before_setup_and_conclusion_beats() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, signals, bundle, records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    label_layer = type(topology.components)(*detach_label_roots(topology.components))
    hide_labels(label_layer)
    beats = mod._teaching_beats(signals, records)
    seen: list[tuple[set[str], set[str]]] = []
    scene = RecordingScene()

    def visible_labels() -> tuple[set[str], set[str]]:
        scene_root = VGroup(*scene.added) if scene.added else label_layer
        component_labels = {
            label.text
            for label in iter_label_roots(scene_root, roles=("component_label",))
            if label_visible(label)
        }
        net_labels = {
            label.text
            for label in iter_label_roots(scene_root, roles=("net_label",))
            if label_visible(label)
        }
        return component_labels, net_labels

    def fake_beat(scene, sig, **kwargs):
        del scene, sig, kwargs
        seen.append(visible_labels())

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        PropagationSequence(
            layout=layout,
            graph=graph,
            beats=beats,
            bundle=bundle,
            sync_signals=signals,
            panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
            topology=topology,
            label_layer=label_layer,
        ).play(scene)
    finally:
        ps_mod.play_propagation_beat = original

    assert seen[0][0] == {"IN", "VCC", "GND", "P1", "N1"}
    assert seen[0][1] == set()
    assert seen[1][0] == {"IN", "VCC", "GND", "P1", "N1"}
    assert seen[1][1] == {"OUT"}


def test_sequence_adds_short_settle_after_label_focus_before_beat() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, signals, bundle, records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    label_layer = type(topology.components)(*detach_label_roots(topology.components))
    hide_labels(label_layer)
    beats = mod._teaching_beats(signals, records)
    scene = RecordingScene()
    sequence = PropagationSequence(
        layout=layout,
        graph=graph,
        beats=beats,
        bundle=bundle,
        sync_signals=signals,
        panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
        topology=topology,
        label_layer=label_layer,
    )
    setup_style = sequence._resolve_style(beats[0])
    conclusion_style = sequence._resolve_style(beats[1])
    conclusion_focus_plan = sequence._build_topology_focus_plan(
        beats[1],
        conclusion_style,
        profile=sequence._resolve_transition_profile(beats[1]),
    )

    def fake_beat(scene, sig, **kwargs):
        del scene, sig, kwargs

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        sequence.play(scene)
    finally:
        ps_mod.play_propagation_beat = original

    waits = scene.waited
    assert waits == [
        pytest.approx(sequence._topology_focus_settle_duration(beats[0], setup_style)),
        pytest.approx(sequence._label_focus_settle_duration(beats[0], setup_style, label_count=5)),
        pytest.approx(sequence._post_beat_hold(beats[0], setup_style)),
        pytest.approx(setup_style.beat_gap),
        pytest.approx(
            sequence._topology_focus_settle_duration(
                beats[1],
                conclusion_style,
                endpoint_emphasis=conclusion_focus_plan.endpoint_emphasis,
                animation_count=len(conclusion_focus_plan.animations),
            )
        ),
        pytest.approx(
            sequence._label_focus_settle_duration(beats[1], conclusion_style, label_count=1)
        ),
        pytest.approx(sequence._post_beat_hold(beats[1], conclusion_style)),
    ]


def test_sequence_trace_records_director_subphases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mod = _load_cmos_module()
    graph, elements, layout, signals, bundle, records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    label_layer = type(topology.components)(*detach_label_roots(topology.components))
    hide_labels(label_layer)
    beats = mod._teaching_beats(signals, records)
    scene = RecordingScene()

    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()

    def fake_beat(scene, sig, **kwargs):
        del scene
        record_stage(
            "beat.play",
            beat_index=kwargs.get("beat_index"),
            signal_name=sig.name,
            run_time=kwargs["duration"],
            purpose="propagation",
        )

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        PropagationSequence(
            layout=layout,
            graph=graph,
            beats=beats,
            bundle=bundle,
            sync_signals=signals,
            panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
            topology=topology,
            label_layer=label_layer,
            caption_callback=lambda _spec, _i: None,
        ).play(scene)
    finally:
        ps_mod.play_propagation_beat = original

    trace_path = flush_trace(scene)
    assert trace_path is not None
    payload = json.loads(trace_path.read_text(encoding="utf-8"))
    stages = [entry["stage"] for entry in payload["stages"]]

    expected = [
        "sequence.beat_start",
        "sequence.topology_focus",
        "sequence.topology_focus_settle",
        "sequence.caption_settle",
        "sequence.label_focus",
        "sequence.label_focus_settle",
        "beat.play",
        "sequence.beat_end",
        "sequence.post_hold",
    ]
    assert stages[:9] == expected
    beat_start_entry = payload["stages"][0]
    assert beat_start_entry["detail"]["from_pin_id"] == beats[0].record.from_pin_id
    assert beat_start_entry["detail"]["to_pin_id"] == beats[0].record.to_pin_id
    assert beat_start_entry["detail"]["reveal_target_count"] == 1
    assert beat_start_entry["detail"]["reveal_signal_names"] == [beats[0].signal.name]
    label_focus_entry = payload["stages"][4]
    assert label_focus_entry["beat_index"] == 0
    assert label_focus_entry["purpose"] == "focus"
    assert label_focus_entry["run_time"] > 0.0
    assert label_focus_entry["detail"]["transition_profile"] == "setup"
    label_focus_settle_entry = next(
        entry for entry in payload["stages"] if entry["stage"] == "sequence.label_focus_settle"
    )
    assert label_focus_settle_entry["detail"]["label_count"] == 5
    topology_focus_settle_entries = [
        entry for entry in payload["stages"] if entry["stage"] == "sequence.topology_focus_settle"
    ]
    assert topology_focus_settle_entries[0]["detail"]["endpoint_emphasis"] is False
    assert topology_focus_settle_entries[0]["detail"]["animation_count"] == 1
    assert topology_focus_settle_entries[1]["detail"]["endpoint_emphasis"] is True
    assert topology_focus_settle_entries[1]["detail"]["animation_count"] == 2
    topology_focus_entries = [
        entry for entry in payload["stages"] if entry["stage"] == "sequence.topology_focus"
    ]
    assert topology_focus_entries[0]["detail"]["from_pin_id"] == beats[0].record.from_pin_id
    assert topology_focus_entries[0]["detail"]["to_pin_id"] == beats[0].record.to_pin_id
    assert topology_focus_entries[0]["detail"]["endpoint_emphasis"] is False
    assert topology_focus_entries[0]["detail"]["animation_count"] == 1
    assert topology_focus_entries[1]["detail"]["endpoint_emphasis"] is True
    assert topology_focus_entries[1]["detail"]["animation_count"] == 2
    caption_settle_entry = next(
        entry for entry in payload["stages"] if entry["stage"] == "sequence.caption_settle"
    )
    assert caption_settle_entry["detail"]["from_pin_id"] == beats[0].record.from_pin_id
    assert caption_settle_entry["detail"]["to_pin_id"] == beats[0].record.to_pin_id
    assert caption_settle_entry["detail"]["reveal_target_count"] == 1
    assert caption_settle_entry["detail"]["caption_len"] == len(beats[0].caption or "")
    post_hold_entry = next(
        entry for entry in payload["stages"] if entry["stage"] == "sequence.post_hold"
    )
    assert post_hold_entry["detail"]["from_pin_id"] == beats[0].record.from_pin_id
    assert post_hold_entry["detail"]["to_pin_id"] == beats[0].record.to_pin_id
    assert post_hold_entry["detail"]["caption_len"] == len(beats[0].caption or "")
    assert post_hold_entry["detail"]["reveal_target_count"] == 1


def test_nondimmed_setup_sequence_adds_topology_focus_stage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    mod = _load_cmos_module()
    graph, elements, layout, signals, bundle, records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    scene = RecordingScene()
    beats = mod._teaching_beats(signals, records)
    seq = PropagationSequence(
        layout=layout,
        graph=graph,
        beats=beats[:1],
        bundle=bundle,
        sync_signals=signals,
        panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
        topology=topology,
        dim_inactive=False,
    )
    resolved = seq._resolve_style(beats[0])

    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()

    def fake_beat(scene, sig, **kwargs):
        del scene
        record_stage(
            "beat.play",
            beat_index=kwargs.get("beat_index"),
            signal_name=sig.name,
            run_time=kwargs["duration"],
            purpose="propagation",
        )

    import manim_engineering.animation.propagation_sequence as ps_mod

    original = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        seq.play(scene)
    finally:
        ps_mod.play_propagation_beat = original

    trace_path = flush_trace(scene)
    assert trace_path is not None
    assert trace_stage_names(trace_path)[:3] == [
        "sequence.beat_start",
        "sequence.topology_focus",
        "sequence.topology_focus_settle",
    ]
    assert scene.run_times[0] == pytest.approx(seq._topology_focus_duration(beats[0], resolved))
    assert scene.waited[0] == pytest.approx(seq._topology_focus_settle_duration(beats[0], resolved))
    assert getattr(scene.played[0][0], "animations", None) is None


def test_dimmed_sequence_adds_explicit_topology_focus_stage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    graph, layout, signal = _three_beat_signal_fixture()
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    scene = RecordingScene()
    projection = TopologyProjection(components=VGroup(), wires=VGroup(), n_components=0)
    seq = PropagationSequence(
        signal,
        layout=layout,
        graph=graph,
        max_beats=1,
        dim_inactive=True,
        topology=projection,
    )
    spec = seq.beats[0]
    resolved = seq._resolve_style(spec)

    def fake_beat(scene, sig, **kwargs):
        del scene
        record_stage(
            "beat.play",
            beat_index=kwargs.get("beat_index"),
            signal_name=sig.name,
            run_time=kwargs["duration"],
            purpose="propagation",
        )

    import manim_engineering.animation.propagation_sequence as ps_mod

    original_beat = ps_mod.play_propagation_beat
    ps_mod.play_propagation_beat = fake_beat
    try:
        seq.play(scene)
    finally:
        ps_mod.play_propagation_beat = original_beat
    path = flush_trace(scene)
    assert path is not None
    assert trace_stage_names(path) == [
        "sequence.beat_start",
        "sequence.topology_focus",
        "beat.play",
        "sequence.beat_end",
    ]
    assert scene.waited == []
    assert scene.run_times[0] == pytest.approx(seq._topology_focus_duration(spec, resolved))
