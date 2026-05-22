"""Base types for reusable animation primitives."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from manim import Animation, VMobject

from manim_engineering.animation.purpose import AnimationPurpose

SelfT = TypeVar("SelfT", bound="AnimationPrimitive")


@dataclass(frozen=True)
class AnimationPlan:
    """Mobjects to add and animations to play (no Scene coupling)."""

    overlays: tuple[VMobject, ...]
    animations: tuple[Animation, ...]
    run_time: float


class AnimationPrimitive(ABC, Generic[SelfT]):
    """Purpose-tagged primitive with explicit duration control."""

    purpose: AnimationPurpose

    def __init__(self, *, duration: float) -> None:
        self._duration = duration

    @property
    def duration(self) -> float:
        return self._duration

    def set_duration(self, duration: float) -> SelfT:
        """Return self after updating run time (fluent API)."""
        if duration <= 0:
            msg = f"duration must be positive, got {duration}"
            raise ValueError(msg)
        self._duration = duration
        return self  # type: ignore[return-value]

    @abstractmethod
    def build(self) -> AnimationPlan:
        """Build overlays and animations without mutating semantic topology."""
