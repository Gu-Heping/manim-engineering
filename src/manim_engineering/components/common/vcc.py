"""VCC power supply symbol."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.semantic.enums import PinDirection, SignalType

_VCC_BOUNDS = Bounds(width=0.4, height=0.4)
_VCC_ANCHORS: dict[str, AnchorPoint] = {
    "vcc": (0.5, 1.0),
    "center": (0.5, 0.5),
}


class VCC(CircuitElement):
    """Power rail with pin ``vcc``."""

    semantic_type = "power"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_VCC_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _VCC_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "vcc",
            direction=PinDirection.OUT,
            signal_type=SignalType.POWER,
            routing_hints=("vertical", "up"),
        )
