"""Single-beat orchestration: parallel SignalFlow + WaveformSync."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from manim import AnimationGroup, FadeOut, VGroup

from manim_engineering.animation.analog_ramp import AnalogRamp
from manim_engineering.animation.base import AnimationPlan
from manim_engineering.animation.layers import PROPAGATION_Z_INDEX, PULSE_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION, OVERLAY_FADE_OUT
from manim_engineering.animation.scene_protocol import (
    TeachingSceneProtocol,
    require_scene_methods,
)
from manim_engineering.animation.signal_flow import SignalFlow
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.animation.waveform_sync import WaveformSync
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


def _fade_out_and_remove(scene: TeachingSceneProtocol, *mobjects: object) -> None:
    """Fade overlays out briefly, then remove so beats do not stack ghosts."""
    if not mobjects:
        return
    if OVERLAY_FADE_OUT > 0:
        scene.play(
            *[FadeOut(mob, run_time=OVERLAY_FADE_OUT) for mob in mobjects],
            run_time=OVERLAY_FADE_OUT,
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
    reveal_tracker: WaveformRevealTracker | None = None,
    reveal_targets: Sequence[tuple[Signal, int]] = (),
    reveal_time: float | None = None,
    reveal_scope: Literal["all", "signal"] = "all",
    wire_pulse: bool = True,
) -> float:
    """
    Play propagation and optional waveform timing on the same beat (one ``run_time``).

    Returns the beat duration used. After the animation completes, every
    overlay/propagation mobject added by this beat is faded out and removed
    so a subsequent beat does not stack ghost VGroups on top of the topology.
    """
    beat_duration = duration if duration is not None else BEAT_DURATION

    if wire_pulse:
        flow = SignalFlow(
            signal,
            record=record,
            layout=layout,
            graph=graph,
            duration=beat_duration,
        )
        flow_plan = flow.build()
    else:
        flow_plan = AnimationPlan(
            overlays=(),
            propagation_overlays=(),
            animations=(),
            run_time=beat_duration,
        )

    sync_plan = None
    ramp_plan = None
    ramp_t_start = 0.0
    if reveal_tracker is not None:
        ramp_t_start = reveal_tracker.revealed_time_for(signal.name)

    if bundle is not None and panel_spec is not None and signals:
        trace_match = bundle.trace_named(signal.name)
        use_ramp = (
            reveal_time is not None
            and trace_match is not None
            and not trace_match.is_discrete
        )
        if use_ramp:
            trace_index = next(
                index
                for index, trace in enumerate(bundle.traces)
                if trace.signal_name == signal.name
            )
            ramp = AnalogRamp(
                trace_match,
                panel_spec=panel_spec,
                trace_index=trace_index,
                t_start=ramp_t_start,
                t_end=reveal_time,
                duration=beat_duration,
            )
            ramp_plan = ramp.build()
        else:
            sync = WaveformSync(
                bundle,
                signals,
                panel_spec=panel_spec,
                beat=beat,
                duration=beat_duration,
                active_signal=signal,
            )
            sync_plan = sync.build()

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
    _fade_out_and_remove(scene, *to_remove)

    return beat_duration
