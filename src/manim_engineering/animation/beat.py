"""Single-beat orchestration: parallel SignalFlow + WaveformSync."""

from __future__ import annotations

from collections.abc import Sequence

from manim import AnimationGroup, FadeOut, VGroup

from manim_engineering.animation.layers import PROPAGATION_Z_INDEX, PULSE_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION, OVERLAY_FADE_OUT
from manim_engineering.animation.signal_flow import SignalFlow
from manim_engineering.animation.waveform_sync import WaveformSync
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle


def _fade_out_and_remove(scene: object, *mobjects: object) -> None:
    """Fade overlays out briefly, then remove so beats do not stack ghosts."""
    play = getattr(scene, "play", None)
    remove = getattr(scene, "remove", None)
    if not mobjects:
        return
    if play is not None and OVERLAY_FADE_OUT > 0:
        play(
            *[FadeOut(mob, run_time=OVERLAY_FADE_OUT) for mob in mobjects],
            run_time=OVERLAY_FADE_OUT,
        )
    if remove is not None:
        remove(*mobjects)


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
) -> float:
    """
    Play propagation and optional waveform timing on the same beat (one ``run_time``).

    Returns the beat duration used. After the animation completes, every
    overlay/propagation mobject added by this beat is faded out and removed
    so a subsequent beat does not stack ghost VGroups on top of the topology.
    """
    beat_duration = duration if duration is not None else BEAT_DURATION

    flow = SignalFlow(
        signal,
        record=record,
        layout=layout,
        graph=graph,
        duration=beat_duration,
    )
    flow_plan = flow.build()

    sync_plan = None
    if bundle is not None and panel_spec is not None and signals:
        sync = WaveformSync(
            bundle,
            signals,
            panel_spec=panel_spec,
            beat=beat,
            duration=beat_duration,
            active_signal=signal,
        )
        sync_plan = sync.build()

    add = getattr(scene, "add", None)
    play = getattr(scene, "play", None)
    if add is None or play is None:
        msg = "scene must provide add() and play() like manim.Scene"
        raise TypeError(msg)

    propagation_overlays = list(flow_plan.propagation_overlays)
    if sync_plan is not None:
        propagation_overlays.extend(sync_plan.propagation_overlays)

    propagation_group: VGroup | None = None
    if propagation_overlays:
        propagation_group = VGroup(*propagation_overlays)
        propagation_group.set_z_index(PROPAGATION_Z_INDEX)
        add(propagation_group)

    overlays = list(flow_plan.overlays)
    if sync_plan is not None:
        overlays.extend(sync_plan.overlays)
    if overlays:
        for mob in overlays:
            if hasattr(mob, "set_z_index"):
                mob.set_z_index(PULSE_Z_INDEX)
        add(*overlays)

    animations: list[object] = []
    for anim in flow_plan.animations:
        animations.append(anim)
    if sync_plan is not None:
        for anim in sync_plan.animations:
            animations.append(anim)

    if animations:
        if len(animations) == 1:
            combined = animations[0]
        else:
            combined = AnimationGroup(*animations)
        play(combined, run_time=beat_duration)

    to_remove: list[object] = []
    if propagation_group is not None:
        to_remove.append(propagation_group)
    if overlays:
        to_remove.extend(overlays)
    _fade_out_and_remove(scene, *to_remove)

    return beat_duration
