"""Ground reference symbol."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_GROUND_BOUNDS = Bounds(width=0.4, height=0.4)
_GROUND_ANCHORS: dict[str, AnchorPoint] = {
    # Top-centre: vertical-stack schematics connect upward into GND.
    "gnd": (0.5, 1.0),
    "center": (0.5, 0.5),
}


class Ground(CircuitElement):
    """Ground reference with pin ``gnd``."""

    semantic_type = "power"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_GROUND_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _GROUND_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "gnd",
            direction=PinDirection.IN,
            signal_type=SignalType.GROUND,
            routing_hints=("vertical", "down"),
        )
