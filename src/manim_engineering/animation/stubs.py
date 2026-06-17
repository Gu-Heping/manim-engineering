"""Small standalone animation primitives for local state emphasis."""

from __future__ import annotations

from collections.abc import Sequence

from manim import AnimationGroup, Circle, Create, FadeOut, Rectangle

import manim_engineering.animation.theme as anim_theme
from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.layers import PULSE_Z_INDEX, TIMING_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import register_primitive


def _point3(point: Sequence[float]) -> tuple[float, float, float]:
    if len(point) < 2:
        msg = "point must contain at least x and y coordinates"
        raise ValueError(msg)
    z = float(point[2]) if len(point) >= 3 else 0.0
    return (float(point[0]), float(point[1]), z)


@register_primitive("voltage_pulse")
class VoltagePulse(AnimationPrimitive["VoltagePulse"]):
    """Emphasize a local analog voltage point with a warm timing ring."""

    purpose = AnimationPurpose.TIMING

    def __init__(
        self,
        *,
        center: Sequence[float] = (0.0, 0.0, 0.0),
        radius: float = 0.18,
        color: object = anim_theme.HIGHLIGHT_COLOR,
        stroke_width: float = 4.0,
        duration: float = BEAT_DURATION * 0.45,
    ) -> None:
        super().__init__(duration=duration)
        if radius <= 0.0:
            msg = f"radius must be positive, got {radius}"
            raise ValueError(msg)
        if stroke_width <= 0.0:
            msg = f"stroke_width must be positive, got {stroke_width}"
            raise ValueError(msg)
        self._center = _point3(center)
        self._radius = radius
        self._color = color
        self._stroke_width = stroke_width

    def build(self) -> AnimationPlan:
        ring = Circle(radius=self._radius)
        ring.move_to(self._center)
        ring.set_stroke(self._color, width=self._stroke_width, opacity=1.0)
        ring.set_fill(opacity=0.0)
        ring.set_z_index(TIMING_Z_INDEX)
        return AnimationPlan(
            overlays=(ring,),
            animations=(
                AnimationGroup(
                    Create(ring),
                    FadeOut(ring),
                    run_time=self.duration,
                ),
            ),
            run_time=self.duration,
        )


@register_primitive("logic_transition")
class LogicTransition(AnimationPrimitive["LogicTransition"]):
    """Emphasize a discrete logic-state change at a gate or node."""

    purpose = AnimationPurpose.TRANSITION

    def __init__(
        self,
        *,
        center: Sequence[float] = (0.0, 0.0, 0.0),
        width: float = 0.46,
        height: float = 0.28,
        color: object = anim_theme.HIGHLIGHT_COLOR,
        stroke_width: float = 3.0,
        duration: float = BEAT_DURATION * 0.5,
    ) -> None:
        super().__init__(duration=duration)
        if width <= 0.0 or height <= 0.0:
            msg = f"width and height must be positive, got {width} x {height}"
            raise ValueError(msg)
        if stroke_width <= 0.0:
            msg = f"stroke_width must be positive, got {stroke_width}"
            raise ValueError(msg)
        self._center = _point3(center)
        self._width = width
        self._height = height
        self._color = color
        self._stroke_width = stroke_width

    def build(self) -> AnimationPlan:
        marker = Rectangle(width=self._width, height=self._height)
        marker.move_to(self._center)
        marker.set_stroke(self._color, width=self._stroke_width, opacity=1.0)
        marker.set_fill(opacity=0.0)
        marker.set_z_index(PULSE_Z_INDEX)
        return AnimationPlan(
            overlays=(marker,),
            animations=(
                AnimationGroup(
                    Create(marker),
                    FadeOut(marker),
                    run_time=self.duration,
                ),
            ),
            run_time=self.duration,
        )
