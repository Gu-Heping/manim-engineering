"""WaveformSync: timing-purpose animation aligned with propagation beats."""

from __future__ import annotations

from collections.abc import Callable, Sequence

from manim import Animation, AnimationGroup, ShowPassingFlash
from manim.utils.rate_functions import smooth as _DEFAULT_RATE_FUNC

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.layers import TIMING_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import register_primitive
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.wires import path_mobject_from_points
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.immutable import copy_for_animation
from manim_engineering.renderers.minimal.waveform import trace_color
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec, transition_segment_for_beat
from manim_engineering.waveform.trace import WaveformBundle

DEFAULT_TIMING_DURATION = BEAT_DURATION


@register_primitive("waveform_sync")
class WaveformSync(AnimationPrimitive["WaveformSync"]):
    """
    Highlight trace edge transitions on the same beat as :class:`SignalFlow`.

    Uses detached segment copies with ``ShowPassingFlash``; does not mutate
    renderer waveform geometry.
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
        active_signal: Signal | None = None,
        rate_func: Callable[[float], float] = _DEFAULT_RATE_FUNC,
        flash_time_width: float = 0.65,
    ) -> None:
        super().__init__(duration=duration)
        self._bundle = bundle
        self._signals = tuple(signals)
        self._panel_spec = panel_spec
        self._beat = beat
        self._active_signal = active_signal
        self._rate_func = rate_func
        self._flash_time_width = flash_time_width

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
        animations: list[Animation] = []
        propagation_overlays: list[object] = []

        for trace_index, trace in enumerate(self._bundle.traces):
            if self._active_signal is not None:
                if trace.signal_name != self._active_signal.name:
                    continue
            segment = transition_segment_for_beat(
                trace,
                beat,
                self._panel_spec,
                trace_index,
            )
            if segment is None or len(segment) < 2:
                continue
            path = path_mobject_from_points(segment)
            path.set_stroke(
                color=trace_color(trace),
                width=theme.WAVEFORM_STROKE_WIDTH,
                opacity=1.0,
            )
            flash_target = copy_for_animation(path)
            flash_target.set_z_index(TIMING_Z_INDEX)
            propagation_overlays.append(flash_target)
            animations.append(
                ShowPassingFlash(
                    flash_target,
                    time_width=self._flash_time_width,
                    run_time=self.duration,
                    rate_func=self._rate_func,
                )
            )

        if not animations:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

        group = AnimationGroup(*animations) if len(animations) > 1 else animations[0]
        return AnimationPlan(
            overlays=(),
            propagation_overlays=tuple(propagation_overlays),
            animations=(group,),
            run_time=self.duration,
        )

    def play(self, scene: object) -> None:
        plan = self.build()
        scene = require_scene_methods(scene, require_play=True, require_add=True)
        if plan.propagation_overlays:
            from manim import VGroup

            timing = VGroup(*plan.propagation_overlays)
            timing.set_z_index(TIMING_Z_INDEX)
            scene.add(timing)
        scene.add(*plan.overlays)
        scene.play(*plan.animations, run_time=plan.run_time)

    def aligns_with_signal_flow(self, flow_duration: float) -> bool:
        """Same run_time as a paired SignalFlow (sync contract)."""
        return self.duration == flow_duration
