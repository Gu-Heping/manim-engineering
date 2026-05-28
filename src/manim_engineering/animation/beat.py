"""Single-beat orchestration: parallel SignalFlow + WaveformSync."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from manim import AnimationGroup, Create, FadeOut, LaggedStart, VGroup

from manim_engineering.animation.base import AnimationPlan
from manim_engineering.animation.beat_factory import TimingMode, build_beat_plans
from manim_engineering.animation.layers import PROPAGATION_Z_INDEX, PULSE_Z_INDEX
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.scene_protocol import (
    TeachingSceneProtocol,
    require_scene_methods,
)
from manim_engineering.animation.stage_record import record_signal_stage
from manim_engineering.animation.style import TeachingStyle
from manim_engineering.animation.trace import record_stage
from manim_engineering.animation.waveform_controller import WaveformSegmentController
from manim_engineering.animation.waveform_reveal import (
    SegmentRevealPlan,
    WaveformRevealTracker,
    commit_beat_reveal,
    mount_reveal_plan,
)
from manim_engineering.animation.wires import path_mobject_from_points
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle


@dataclass(frozen=True)
class _WaveformCommitPhase:
    reveal_anims: tuple[object, ...]
    reveal_commit_overlays: tuple[object, ...]
    new_lines: tuple[object, ...]


@dataclass(frozen=True)
class _TimingAccentPhase:
    purpose: str | None
    sync_animation_count: int
    ramp_animation_count: int
    propagation_overlays: tuple[object, ...]
    overlays: tuple[object, ...]
    animations: tuple[object, ...]


@dataclass(frozen=True)
class _PlaybackPhase:
    propagation_overlays: tuple[object, ...]
    overlays: tuple[object, ...]
    flow_anims: tuple[object, ...]


@dataclass(frozen=True)
class _BeatExecutionPlan:
    waveform_commit: _WaveformCommitPhase
    timing_accent: _TimingAccentPhase
    playback: _PlaybackPhase


@dataclass(frozen=True)
class _BeatPhaseDurations:
    waveform_commit: float
    commit_settle: float
    timing_accent: float
    timing_settle: float
    playback: float


def _resolved_record(signal: Signal, record: PropagationRecord | None) -> PropagationRecord | None:
    if record is not None:
        return record
    history = signal.propagation_history
    if not history:
        return None
    return history[-1]


def _phase_durations(
    beat_duration: float,
    *,
    has_waveform_commit: bool,
    has_timing_accent: bool,
    has_playback: bool,
    commit_line_count: int = 0,
    commit_overlay_count: int = 0,
) -> _BeatPhaseDurations:
    if has_waveform_commit:
        if not has_playback:
            return _BeatPhaseDurations(
                waveform_commit=beat_duration,
                commit_settle=0.0,
                timing_accent=0.0,
                timing_settle=0.0,
                playback=0.0,
            )
        commit_duration = min(max(beat_duration * 0.35, 0.16), beat_duration * 0.5)
        if beat_duration - commit_duration < 0.12:
            commit_duration = max(beat_duration - 0.12, beat_duration * 0.25)
        remaining = max(beat_duration - commit_duration, 0.0)
        settle_base = max(beat_duration * 0.05, 0.025)
        settle_extra = min(max(commit_line_count - 1, 0) * 0.005, 0.015)
        if commit_overlay_count > 0:
            settle_extra += 0.01
        settle_duration = min(
            settle_base + settle_extra,
            0.065,
            max(remaining - 0.12, 0.0),
        )
        return _BeatPhaseDurations(
            waveform_commit=commit_duration,
            commit_settle=settle_duration,
            timing_accent=0.0,
            timing_settle=0.0,
            playback=max(remaining - settle_duration, 0.0),
        )
    if has_timing_accent and has_playback:
        accent_duration = min(max(beat_duration * 0.28, 0.16), beat_duration * 0.45)
        if beat_duration - accent_duration < 0.12:
            accent_duration = max(beat_duration - 0.12, beat_duration * 0.2)
        remaining = max(beat_duration - accent_duration, 0.0)
        settle_duration = min(
            max(beat_duration * 0.04, 0.025),
            0.05,
            max(remaining - 0.12, 0.0),
        )
        return _BeatPhaseDurations(
            waveform_commit=0.0,
            commit_settle=0.0,
            timing_accent=accent_duration,
            timing_settle=settle_duration,
            playback=max(remaining - settle_duration, 0.0),
        )
    if has_timing_accent:
        return _BeatPhaseDurations(
            waveform_commit=0.0,
            commit_settle=0.0,
            timing_accent=beat_duration,
            timing_settle=0.0,
            playback=0.0,
        )
    return _BeatPhaseDurations(
        waveform_commit=0.0,
        commit_settle=0.0,
        timing_accent=0.0,
        timing_settle=0.0,
        playback=beat_duration,
    )


def _line_points(lines: Sequence[object]) -> tuple[Point2D, ...]:
    if not lines:
        return ()
    points: list[Point2D] = []
    for index, line in enumerate(lines):
        start = line.get_start()
        end = line.get_end()
        start_point = Point2D(float(start[0]), float(start[1]))
        end_point = Point2D(float(end[0]), float(end[1]))
        if index == 0:
            points.append(start_point)
        elif abs(points[-1].x - start_point.x) > 1e-6 or abs(points[-1].y - start_point.y) > 1e-6:
            return ()
        points.append(end_point)
    return tuple(points)


def _is_diagonal(line: object) -> bool:
    start = line.get_start()
    end = line.get_end()
    return (
        abs(float(start[0]) - float(end[0])) > 1e-6
        and abs(float(start[1]) - float(end[1])) > 1e-6
    )


def _continuous_commit_overlay(lines: Sequence[object]) -> object | None:
    """Single-path commit for smooth analog reveals; digital step segments keep per-line Create."""
    if len(lines) < 2 or not any(_is_diagonal(line) for line in lines):
        return None
    points = _line_points(lines)
    if len(points) < 2:
        return None
    path = path_mobject_from_points(points)
    first = lines[0]
    path.set_stroke(
        color=first.get_stroke_color(),
        width=first.get_stroke_width(),
        opacity=1.0,
    )
    return path


def _merge_animation_plans(
    *plans: AnimationPlan | None,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    propagation_overlays: list[object] = []
    overlays: list[object] = []
    animations: list[object] = []
    for plan in plans:
        if plan is None:
            continue
        propagation_overlays.extend(plan.propagation_overlays)
        overlays.extend(plan.overlays)
        animations.extend(plan.animations)
    return tuple(propagation_overlays), tuple(overlays), tuple(animations)


def _build_execution_plan(
    signal: Signal,
    *,
    waveform_controller: WaveformSegmentController | None,
    reveal_time: float | None,
    reveal_scope: Literal["all", "signal"],
    reveal_targets: Sequence[tuple[Signal, int]],
    flow_plan: AnimationPlan,
    sync_plan: AnimationPlan | None,
    ramp_plan: AnimationPlan | None,
    timing_purpose: str | None,
) -> _BeatExecutionPlan:
    reveal_anims: list[object] = []
    reveal_commit_overlays: list[object] = []
    new_lines: list[object] = []
    resolved_sync = sync_plan
    resolved_ramp = ramp_plan
    resolved_timing_purpose = timing_purpose
    if waveform_controller is not None:
        reveal_plans: list[SegmentRevealPlan] = []
        if reveal_time is not None:
            if reveal_scope == "signal":
                plan = waveform_controller.plan_reveal_for_time_on_signal(signal.name, reveal_time)
                if plan.added or plan.removed:
                    reveal_plans.append(plan)
            else:
                reveal_plans.extend(waveform_controller.plan_reveal_for_time(reveal_time))
        elif reveal_targets:
            for reveal_signal, target_beat in reveal_targets:
                plan = waveform_controller.plan_reveal_for_beat(reveal_signal, target_beat)
                if plan.added or plan.removed:
                    reveal_plans.append(plan)
        for plan in reveal_plans:
            plan_lines = mount_reveal_plan(plan)
            new_lines.extend(plan_lines)
            commit_overlay = _continuous_commit_overlay(plan_lines)
            if commit_overlay is not None:
                reveal_commit_overlays.append(commit_overlay)
                reveal_anims.append(Create(commit_overlay))
            elif len(plan_lines) == 1:
                reveal_anims.append(Create(plan_lines[0]))
            elif plan_lines:
                reveal_anims.append(
                    LaggedStart(*[Create(line) for line in plan_lines], lag_ratio=0.1)
                )

    if new_lines:
        resolved_sync = None
        resolved_ramp = None
        resolved_timing_purpose = None

    timing_propagation_overlays, timing_overlays, timing_anims = _merge_animation_plans(
        resolved_sync, resolved_ramp
    )
    return _BeatExecutionPlan(
        waveform_commit=_WaveformCommitPhase(
            reveal_anims=tuple(reveal_anims),
            reveal_commit_overlays=tuple(reveal_commit_overlays),
            new_lines=tuple(new_lines),
        ),
        timing_accent=_TimingAccentPhase(
            purpose=resolved_timing_purpose,
            sync_animation_count=0 if resolved_sync is None else len(resolved_sync.animations),
            ramp_animation_count=0 if resolved_ramp is None else len(resolved_ramp.animations),
            propagation_overlays=timing_propagation_overlays,
            overlays=timing_overlays,
            animations=timing_anims,
        ),
        playback=_PlaybackPhase(
            propagation_overlays=tuple(flow_plan.propagation_overlays),
            overlays=tuple(flow_plan.overlays),
            flow_anims=tuple(flow_plan.animations),
        ),
    )


def _fade_out_and_remove(
    scene: TeachingSceneProtocol,
    style: TeachingStyle,
    *mobjects: object,
) -> None:
    """Fade overlays out briefly, then remove so beats do not stack ghosts."""
    if not mobjects:
        return
    if style.overlay_fade_out > 0:
        scene.play(
            *[FadeOut(mob, run_time=style.overlay_fade_out) for mob in mobjects],
            run_time=style.overlay_fade_out,
        )
    scene.remove(*mobjects)


def _record_beat_stage(
    signal: Signal,
    stage: str,
    *,
    beat_duration: float,
    beat: int | None,
    beat_index: int | None,
    purpose: str | None = None,
    record: PropagationRecord | None = None,
    reveal_time: float | None = None,
    reveal_scope: Literal["all", "signal"] | None = None,
    reveal_targets: Sequence[tuple[Signal, int]] = (),
    **detail: object,
) -> None:
    common_detail: dict[str, object] = {}
    if record is not None:
        common_detail["from_pin_id"] = record.from_pin_id
        common_detail["to_pin_id"] = record.to_pin_id
    if reveal_time is not None:
        common_detail["reveal_time"] = reveal_time
        if reveal_scope is not None:
            common_detail["reveal_scope"] = reveal_scope
    if reveal_targets:
        common_detail["reveal_target_count"] = len(reveal_targets)
        common_detail["reveal_signal_names"] = [
            reveal_signal.name for reveal_signal, _target in reveal_targets
        ]
    record_signal_stage(
        stage,
        signal_name=signal.name,
        run_time=beat_duration,
        beat_index=beat_index if beat_index is not None else beat,
        purpose=purpose,
        record=record_stage,
        **common_detail,
        **detail,
    )


def _record_execution_stages(
    signal: Signal,
    execution: _BeatExecutionPlan,
    *,
    phase_durations: _BeatPhaseDurations,
    beat: int | None,
    beat_index: int | None,
    record: PropagationRecord | None,
    reveal_time: float | None,
    reveal_scope: Literal["all", "signal"],
    reveal_targets: Sequence[tuple[Signal, int]],
    timing_mode: TimingMode,
    wire_pulse: bool,
) -> None:
    if execution.waveform_commit.new_lines:
        _record_beat_stage(
            signal,
            "beat.waveform_commit",
            beat=beat,
            beat_index=beat_index,
            beat_duration=phase_durations.waveform_commit,
            purpose=AnimationPurpose.TRANSITION.value,
            record=record,
            reveal_time=reveal_time,
            reveal_scope=reveal_scope,
            reveal_targets=reveal_targets,
            line_count=len(execution.waveform_commit.new_lines),
            overlay_count=len(execution.waveform_commit.reveal_commit_overlays),
            animation_count=len(execution.waveform_commit.reveal_anims),
        )

    if execution.timing_accent.purpose is not None:
        _record_beat_stage(
            signal,
            "beat.timing_accent",
            beat=beat,
            beat_index=beat_index,
            beat_duration=phase_durations.timing_accent,
            purpose=execution.timing_accent.purpose,
            record=record,
            reveal_time=reveal_time,
            reveal_scope=reveal_scope,
            reveal_targets=reveal_targets,
            timing_mode=timing_mode,
            sync_animation_count=execution.timing_accent.sync_animation_count,
            ramp_animation_count=execution.timing_accent.ramp_animation_count,
            propagation_overlay_count=len(execution.timing_accent.propagation_overlays),
            overlay_count=len(execution.timing_accent.overlays),
            animation_count=len(execution.timing_accent.animations),
        )

    if phase_durations.timing_settle > 0:
        _record_beat_stage(
            signal,
            "beat.timing_settle",
            beat=beat,
            beat_index=beat_index,
            beat_duration=phase_durations.timing_settle,
            purpose=AnimationPurpose.TRANSITION.value,
            record=record,
            reveal_time=reveal_time,
            reveal_scope=reveal_scope,
            reveal_targets=reveal_targets,
            timing_mode=timing_mode,
            sync_animation_count=execution.timing_accent.sync_animation_count,
            ramp_animation_count=execution.timing_accent.ramp_animation_count,
        )

    if phase_durations.commit_settle > 0:
        _record_beat_stage(
            signal,
            "beat.commit_settle",
            beat=beat,
            beat_index=beat_index,
            beat_duration=phase_durations.commit_settle,
            purpose=AnimationPurpose.TRANSITION.value,
            record=record,
            reveal_time=reveal_time,
            reveal_scope=reveal_scope,
            reveal_targets=reveal_targets,
            line_count=len(execution.waveform_commit.new_lines),
            overlay_count=len(execution.waveform_commit.reveal_commit_overlays),
        )

    _record_beat_stage(
        signal,
        "beat.play",
        beat=beat,
        beat_index=beat_index,
        beat_duration=(
            phase_durations.playback
            if execution.playback.flow_anims
            else 0.0
            if execution.waveform_commit.reveal_anims or execution.timing_accent.animations
            else phase_durations.playback
        ),
        purpose=AnimationPurpose.PROPAGATION.value,
        record=record,
        reveal_time=reveal_time,
        reveal_scope=reveal_scope,
        reveal_targets=reveal_targets,
        wire_pulse=wire_pulse,
        timing_mode=timing_mode,
        propagation_overlay_count=len(execution.playback.propagation_overlays),
        overlay_count=len(execution.playback.overlays),
        animation_count=len(execution.playback.flow_anims),
        timing_purpose=execution.timing_accent.purpose,
    )


def _run_execution_plan(
    scene: TeachingSceneProtocol,
    execution: _BeatExecutionPlan,
    *,
    beat_duration: float,
    phase_durations: _BeatPhaseDurations,
    style: TeachingStyle,
) -> None:
    timing_group: VGroup | None = None
    if execution.timing_accent.propagation_overlays:
        timing_group = VGroup(*execution.timing_accent.propagation_overlays)
        timing_group.set_z_index(PROPAGATION_Z_INDEX)
        scene.add(timing_group)

    if execution.timing_accent.overlays:
        for mob in execution.timing_accent.overlays:
            if hasattr(mob, "set_z_index"):
                mob.set_z_index(PULSE_Z_INDEX)
        scene.add(*execution.timing_accent.overlays)

    propagation_group: VGroup | None = None
    if execution.playback.propagation_overlays:
        propagation_group = VGroup(*execution.playback.propagation_overlays)
        propagation_group.set_z_index(PROPAGATION_Z_INDEX)
        scene.add(propagation_group)

    if execution.playback.overlays:
        for mob in execution.playback.overlays:
            if hasattr(mob, "set_z_index"):
                mob.set_z_index(PULSE_Z_INDEX)
        scene.add(*execution.playback.overlays)

    if execution.waveform_commit.reveal_anims:
        if len(execution.waveform_commit.reveal_anims) == 1:
            scene.play(
                execution.waveform_commit.reveal_anims[0],
                run_time=phase_durations.waveform_commit,
            )
        else:
            scene.play(
                AnimationGroup(*execution.waveform_commit.reveal_anims),
                run_time=phase_durations.waveform_commit,
            )
    if phase_durations.commit_settle > 0:
        scene.wait(phase_durations.commit_settle)

    if execution.timing_accent.animations:
        if len(execution.timing_accent.animations) == 1:
            scene.play(
                execution.timing_accent.animations[0],
                run_time=phase_durations.timing_accent,
            )
        else:
            scene.play(
                AnimationGroup(*execution.timing_accent.animations),
                run_time=phase_durations.timing_accent,
            )
    if phase_durations.timing_settle > 0:
        scene.wait(phase_durations.timing_settle)

    if execution.playback.flow_anims:
        if len(execution.playback.flow_anims) == 1:
            scene.play(
                execution.playback.flow_anims[0],
                run_time=phase_durations.playback,
            )
        else:
            scene.play(
                AnimationGroup(*execution.playback.flow_anims),
                run_time=phase_durations.playback,
            )
    elif not execution.waveform_commit.reveal_anims and not execution.timing_accent.animations:
        scene.wait(beat_duration)

    if execution.waveform_commit.new_lines:
        commit_beat_reveal(execution.waveform_commit.new_lines)
    if execution.waveform_commit.reveal_commit_overlays:
        scene.remove(*execution.waveform_commit.reveal_commit_overlays)

    to_remove: list[object] = []
    if timing_group is not None:
        to_remove.append(timing_group)
    if execution.timing_accent.overlays:
        to_remove.extend(execution.timing_accent.overlays)
    if propagation_group is not None:
        to_remove.append(propagation_group)
    if execution.playback.overlays:
        to_remove.extend(execution.playback.overlays)
    _fade_out_and_remove(scene, style, *to_remove)


def play_propagation_beat(
    scene: object,
    signal: Signal,
    *,
    layout: LayoutResult,
    graph: CircuitGraph | None = None,
    record: PropagationRecord | None = None,
    duration: float | None = None,
    bundle: WaveformBundle | None = None,
    signals: Sequence[Signal] = (),
    panel_spec: WaveformPanelSpec | None = None,
    beat: int | None = None,
    beat_index: int | None = None,
    waveform_controller: WaveformSegmentController | None = None,
    reveal_tracker: WaveformRevealTracker | None = None,
    reveal_targets: Sequence[tuple[Signal, int]] = (),
    reveal_time: float | None = None,
    reveal_scope: Literal["all", "signal"] = "all",
    wire_pulse: bool = True,
    style: TeachingStyle | None = None,
    timing_mode: TimingMode = "auto",
) -> float:
    """
    Play propagation and optional waveform timing on the same beat (one ``run_time``).

    Returns the beat duration used. After the animation completes, every
    overlay/propagation mobject added by this beat is faded out and removed
    so a subsequent beat does not stack ghost VGroups on top of the topology.
    """
    resolved_style = style or TeachingStyle()
    beat_duration = duration if duration is not None else resolved_style.beat_duration
    if waveform_controller is None and reveal_tracker is not None:
        waveform_controller = WaveformSegmentController(reveal_tracker)
    tracker = waveform_controller.tracker if waveform_controller is not None else reveal_tracker
    resolved_record = _resolved_record(signal, record)

    flow_plan, sync_plan, ramp_plan, timing_purpose = build_beat_plans(
        signal,
        layout=layout,
        graph=graph,
        record=record,
        style=resolved_style,
        beat_duration=beat_duration,
        bundle=bundle,
        signals=signals,
        panel_spec=panel_spec,
        beat=beat,
        waveform_controller=waveform_controller,
        reveal_tracker=tracker,
        reveal_time=reveal_time,
        wire_pulse=wire_pulse,
        timing_mode=timing_mode,
    )

    scene = require_scene_methods(
        scene,
        require_play=True,
        require_add=True,
        require_remove=True,
        require_wait=True,
    )

    execution = _build_execution_plan(
        signal,
        waveform_controller=waveform_controller,
        reveal_time=reveal_time,
        reveal_scope=reveal_scope,
        reveal_targets=reveal_targets,
        flow_plan=flow_plan,
        sync_plan=sync_plan,
        ramp_plan=ramp_plan,
        timing_purpose=timing_purpose,
    )
    phase_durations = _phase_durations(
        beat_duration,
        has_waveform_commit=bool(execution.waveform_commit.reveal_anims),
        has_timing_accent=bool(execution.timing_accent.animations),
        has_playback=bool(execution.playback.flow_anims),
        commit_line_count=len(execution.waveform_commit.new_lines),
        commit_overlay_count=len(execution.waveform_commit.reveal_commit_overlays),
    )

    _record_execution_stages(
        signal,
        execution,
        phase_durations=phase_durations,
        beat=beat,
        beat_index=beat_index,
        record=resolved_record,
        reveal_time=reveal_time,
        reveal_scope=reveal_scope,
        reveal_targets=reveal_targets,
        timing_mode=timing_mode,
        wire_pulse=wire_pulse,
    )
    _run_execution_plan(
        scene,
        execution,
        beat_duration=beat_duration,
        phase_durations=phase_durations,
        style=resolved_style,
    )

    return beat_duration
