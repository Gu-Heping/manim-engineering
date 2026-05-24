"""Zener diode symbol stub."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_ZENER_BOUNDS = Bounds(width=0.8, height=0.4)
_ZENER_ANCHORS: dict[str, AnchorPoint] = {
    "anode": (0.0, 0.5),
    "cathode": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class ZenerDiode(CircuitElement):
    """Zener diode — conducts reverse when V > Vz."""

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_ZENER_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _ZENER_BOUNDS

    def _register_pins(self) -> None:
        sig = SignalType.ANALOG
        self._register_pin(
            "anode", direction=PinDirection.IN, signal_type=sig, routing_hints=("horizontal",),
        )
        self._register_pin(
            "cathode", direction=PinDirection.OUT, signal_type=sig, routing_hints=("horizontal",),
        )
