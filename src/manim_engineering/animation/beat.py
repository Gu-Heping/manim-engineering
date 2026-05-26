"""Single-beat orchestration: parallel SignalFlow + WaveformSync."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from manim import AnimationGroup, FadeOut, VGroup

from manim_engineering.animation.base import AnimationPlan
from manim_engineering.animation.beat_factory import TimingMode, build_beat_plans
from manim_engineering.animation.layers import PROPAGATION_Z_INDEX, PULSE_Z_INDEX
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.scene_protocol import (
    TeachingSceneProtocol,
    require_scene_methods,
)
from manim_engineering.animation.style import TeachingStyle
from manim_engineering.animation.trace import record_stage
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.minimal import theme
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle


def _merge_animation_plans(
    flow: AnimationPlan,
    sync: AnimationPlan | None,
    ramp: AnimationPlan | None,
) -> tuple[tuple[object, ...], tuple[object, ...], tuple[object, ...]]:
    propagation_overlays = list(flow.propagation_overlays)
    overlays = list(flow.overlays)
    animations = list(flow.animations)
    for plan in (sync, ramp):
        if plan is None:
            continue
        propagation_overlays.extend(plan.propagation_overlays)
        overlays.extend(plan.overlays)
        animations.extend(plan.animations)
    return tuple(propagation_overlays), tuple(overlays), tuple(animations)


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
        reveal_tracker=reveal_tracker,
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

    propagation_overlays, overlays, flow_anims = _merge_animation_plans(
        flow_plan, sync_plan, ramp_plan
    )

    record_stage(
        "beat.play",
        beat_index=beat_index if beat_index is not None else beat,
        signal_name=signal.name,
        run_time=beat_duration,
        purpose=AnimationPurpose.PROPAGATION.value,
        wire_pulse=wire_pulse,
        timing_mode=timing_mode,
        propagation_overlay_count=len(propagation_overlays),
        overlay_count=len(overlays),
        animation_count=len(flow_anims),
        timing_purpose=timing_purpose,
    )

    propagation_group: VGroup | None = None
    if propagation_overlays:
        propagation_group = VGroup(*propagation_overlays)
        propagation_group.set_z_index(PROPAGATION_Z_INDEX)
        scene.add(propagation_group)

    if overlays:
        for mob in overlays:
            if hasattr(mob, "set_z_index"):
                mob.set_z_index(PULSE_Z_INDEX)
        scene.add(*overlays)

    reveal_anims: list[object] = []
    if reveal_tracker is not None:
        if reveal_time is not None:
            if reveal_scope == "signal":
                lines = reveal_tracker.append_through_time_for(signal.name, reveal_time)
            else:
                lines = reveal_tracker.append_through_time(reveal_time)
            for line in lines:
                reveal_anims.append(line.animate.set_stroke(width=theme.WAVEFORM_STROKE_WIDTH))
        elif reveal_targets:
            for reveal_signal, target_beat in reveal_targets:
                for line in reveal_tracker.append_through_beat(reveal_signal, target_beat):
                    reveal_anims.append(line.animate.set_stroke(width=theme.WAVEFORM_STROKE_WIDTH))

    beat_anims: list[object] = [*reveal_anims, *flow_anims]
    if beat_anims:
        if len(beat_anims) == 1:
            scene.play(beat_anims[0], run_time=beat_duration)
        else:
            scene.play(AnimationGroup(*beat_anims), run_time=beat_duration)
    else:
        scene.wait(beat_duration)

    to_remove: list[object] = []
    if propagation_group is not None:
        to_remove.append(propagation_group)
    if overlays:
        to_remove.extend(overlays)
    _fade_out_and_remove(scene, resolved_style, *to_remove)

    return beat_duration
