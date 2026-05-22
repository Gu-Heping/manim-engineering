"""WaveformSync: timing-purpose animation aligned with propagation beats."""

from __future__ import annotations

from collections.abc import Sequence

from manim import Animation, AnimationGroup, Dot, Indicate

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import register_primitive
from manim_engineering.animation.signal_flow import DEFAULT_PROPAGATION_DURATION
from manim_engineering.renderers.minimal import theme
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec, transition_point_for_beat
from manim_engineering.waveform.trace import WaveformBundle, WaveformTrace

DEFAULT_TIMING_DURATION = DEFAULT_PROPAGATION_DURATION


@register_primitive("waveform_sync")
class WaveformSync(AnimationPrimitive["WaveformSync"]):
    """
    Highlight trace transitions on the same beat as :class:`SignalFlow`.

    Consumes a :class:`WaveformBundle` derived from semantic signals; does not
    propagate or mutate topology.
    """

    purpose = AnimationPurpose.TIMING

    def __init__(
        self,
        bundle: WaveformBundle,
        signals: Sequence[Signal],
        *,
        panel_spec: WaveformPanelSpec,
        beat: int | None = None,
        duration: float = DEFAULT_TIMING_DURATION,
    ) -> None:
        super().__init__(duration=duration)
        self._bundle = bundle
        self._signals = tuple(signals)
        self._panel_spec = panel_spec
        self._beat = beat

    @property
    def bundle(self) -> WaveformBundle:
        return self._bundle

    def resolved_beat(self) -> int:
        if self._beat is not None:
            return self._beat
        max_history = 0
        for signal in self._signals:
            max_history = max(max_history, len(signal.propagation_history))
        return max(0, max_history - 1)

    def build(self) -> AnimationPlan:
        beat = self.resolved_beat()
        overlays: list[Dot] = []
        animations: list[Animation] = []

        for trace_index, trace in enumerate(self._bundle.traces):
            point = transition_point_for_beat(trace, beat, self._panel_spec, trace_index)
            if point is None:
                continue
            marker = Dot(radius=0.05, color=_trace_color(trace))
            marker.move_to([point.x, point.y, 0.0])
            overlays.append(marker)
            animations.append(Indicate(marker, color=theme.WARNING_COLOR, scale_factor=1.4))

        if not animations:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

        group = AnimationGroup(*animations) if len(animations) > 1 else animations[0]
        return AnimationPlan(
            overlays=tuple(overlays),
            animations=(group,),
            run_time=self.duration,
        )

    def play(self, scene: object) -> None:
        plan = self.build()
        add = getattr(scene, "add", None)
        play = getattr(scene, "play", None)
        if add is None or play is None:
            msg = "scene must provide add() and play() like manim.Scene"
            raise TypeError(msg)
        add(*plan.overlays)
        play(*plan.animations, run_time=plan.run_time)

    def aligns_with_signal_flow(self, flow_duration: float) -> bool:
        """Same run_time as a paired SignalFlow (sync contract)."""
        return self.duration == flow_duration


def _trace_color(trace: WaveformTrace) -> object:
    return theme.color_for_signal_type(trace.signal_type)
