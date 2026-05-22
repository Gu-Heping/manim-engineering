"""Layout-oriented types for components (no geometry engine)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.components.exceptions import InvalidBoundsError


@dataclass(frozen=True)
class Bounds:
    """Axis-aligned bounding box in abstract layout units."""

    width: float
    height: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            msg = f"bounds dimensions must be positive: {self.width}×{self.height}"
            raise InvalidBoundsError(msg)
