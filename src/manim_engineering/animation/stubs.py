"""Deferred animation primitives (thin placeholders for Phase 6+)."""

from __future__ import annotations

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.purpose import AnimationPurpose


class VoltagePulse(AnimationPrimitive["VoltagePulse"]):
    """TODO(phase-6): analog voltage emphasis on a node."""

    purpose = AnimationPurpose.TIMING

    def __init__(self, *, duration: float = 0.5) -> None:
        super().__init__(duration=duration)

    def build(self) -> AnimationPlan:
        msg = "VoltagePulse is not implemented yet (planned for Phase 6)"
        raise NotImplementedError(msg)


class LogicTransition(AnimationPrimitive["LogicTransition"]):
    """TODO(phase-6): discrete logic state transition on a gate."""

    purpose = AnimationPurpose.TRANSITION

    def __init__(self, *, duration: float = 0.8) -> None:
        super().__init__(duration=duration)

    def build(self) -> AnimationPlan:
        msg = "LogicTransition is not implemented yet (planned for Phase 6)"
        raise NotImplementedError(msg)
