"""AnalogRamp: timing flash along a continuous waveform segment."""

from __future__ import annotations

from collections.abc import Callable

from manim import Animation, ShowPassingFlash
from manim.utils.rate_functions import smooth as _DEFAULT_RATE_FUNC

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.layers import TIMING_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import register_primitive
from manim_engineering.animation.wires import path_mobject_from_points
from manim_engineering.layout.types import Point2D
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.immutable import copy_for_animation
from manim_engineering.waveform.layout import WaveformPanelSpec, smooth_polyline
from manim_engineering.waveform.trace import WaveformTrace


def segment_points_for_time_range(
    trace: WaveformTrace,
    spec: WaveformPanelSpec,
    trace_index: int,
    *,
    t_start: float,
    t_end: float,
) -> tuple[Point2D, ...]:
    """Clip a smooth polyline to the semantic interval ``[t_start, t_end]``."""
    points = smooth_polyline(
        trace,
        spec,
        trace_index,
        hold_through_time=t_end,
        extend_to_panel=False,
    )
    if not points:
        return ()
    x_start = spec.origin.x + t_start * spec.time_scale
    x_end = spec.origin.x + t_end * spec.time_scale
    clipped: list[Point2D] = []
    for point in points:
        if point.x < x_start - 1e-9:
            continue
        if point.x > x_end + 1e-9:
            break
        clipped.append(point)
    if not clipped:
        return points[:2] if len(points) >= 2 else points
    if clipped[0].x > x_start + 1e-9 and len(points) >= 2:
        prev = next((pt for pt in reversed(points) if pt.x <= x_start + 1e-9), points[0])
        next_pt = next((pt for pt in points if pt.x >= x_start - 1e-9), points[-1])
        if prev.x != next_pt.x:
            y = prev.y + (next_pt.y - prev.y) * (x_start - prev.x) / (next_pt.x - prev.x)
            clipped.insert(0, Point2D(x_start, y))
        else:
            clipped.insert(0, Point2D(x_start, prev.y))
    if clipped[-1].x < x_end - 1e-9:
        clipped.append(Point2D(x_end, clipped[-1].y))
    return tuple(clipped)


@register_primitive("analog_ramp")
class AnalogRamp(AnimationPrimitive["AnalogRamp"]):
    """Highlight a continuous analog segment on the same beat as :class:`SignalFlow`."""

    purpose = AnimationPurpose.TIMING

    def __init__(
        self,
        trace: WaveformTrace,
        *,
        panel_spec: WaveformPanelSpec,
        trace_index: int,
        t_start: float = 0.0,
        t_end: float,
        duration: float = BEAT_DURATION,
        rate_func: Callable[[float], float] = _DEFAULT_RATE_FUNC,
        flash_time_width: float = 0.65,
    ) -> None:
        super().__init__(duration=duration)
        self._trace = trace
        self._panel_spec = panel_spec
        self._trace_index = trace_index
        self._t_start = t_start
        self._t_end = t_end
        self._rate_func = rate_func
        self._flash_time_width = flash_time_width

    def build(self) -> AnimationPlan:
        segment = segment_points_for_time_range(
            self._trace,
            self._panel_spec,
            self._trace_index,
            t_start=self._t_start,
            t_end=self._t_end,
        )
        if len(segment) < 2:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

        path = path_mobject_from_points(segment)
        path.set_stroke(
            color=theme.color_for_signal_type(self._trace.signal_type),
            width=theme.WAVEFORM_STROKE_WIDTH,
            opacity=1.0,
        )
        flash_target = copy_for_animation(path)
        flash_target.set_z_index(TIMING_Z_INDEX)
        animation: Animation = ShowPassingFlash(
            flash_target,
            time_width=self._flash_time_width,
            run_time=self.duration,
            rate_func=self._rate_func,
        )
        return AnimationPlan(
            overlays=(),
            propagation_overlays=(flash_target,),
            animations=(animation,),
            run_time=self.duration,
        )

    def aligns_with_signal_flow(self, flow_duration: float) -> bool:
        return self.duration == flow_duration
