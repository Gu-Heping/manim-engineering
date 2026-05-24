"""Deferred animation primitives — not for production scenes.

``VoltagePulse`` and ``LogicTransition`` raise ``NotImplementedError`` from
``build()``. They exist as registry placeholders for Phase 6+ / Scope B work
(continuous analog emphasis, discrete gate transitions). See **Feature backlog**
in ``docs/ROADMAP.md`` — do not import these in teaching examples until implemented.
"""

from __future__ import annotations

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.purpose import AnimationPurpose


class VoltagePulse(AnimationPrimitive["VoltagePulse"]):
    """Deferred: analog voltage emphasis on a node (Scope B / Phase 6+)."""

    purpose = AnimationPurpose.TIMING

    def __init__(self, *, duration: float = 0.5) -> None:
        super().__init__(duration=duration)

    def build(self) -> AnimationPlan:
        msg = "VoltagePulse is deferred — see docs/ROADMAP.md Feature backlog (Scope B)"
        raise NotImplementedError(msg)


class LogicTransition(AnimationPrimitive["LogicTransition"]):
    """Deferred: discrete logic state transition on a gate (Phase 6+)."""

    purpose = AnimationPurpose.TRANSITION

    def __init__(self, *, duration: float = 0.8) -> None:
        super().__init__(duration=duration)

    def build(self) -> AnimationPlan:
        msg = "LogicTransition is deferred — see docs/ROADMAP.md Feature backlog"
        raise NotImplementedError(msg)
