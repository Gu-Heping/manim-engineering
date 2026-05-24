"""BJT (bipolar junction transistor) symbol stub — NPN and PNP.

Scope A (symbol-only): three pins ``base``, ``collector``, ``emitter``
with the emitter arrow distinguishing NPN (outward) from PNP (inward).
No continuous-physics modelling (Ic = β·Ib, Early effect, etc.) — deferred
to Scope B/C.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_BJT_BOUNDS = Bounds(width=1.0, height=0.8)

_NPN_ANCHORS: dict[str, AnchorPoint] = {
    "base": (0.0, 0.5),
    "collector": (1.0, 1.0),
    "emitter": (1.0, 0.0),
    "center": (0.5, 0.5),
}

_PNP_ANCHORS: dict[str, AnchorPoint] = {
    "base": (0.0, 0.5),
    "collector": (1.0, 0.0),
    "emitter": (1.0, 1.0),
    "center": (0.5, 0.5),
}

_PIN_KWARGS: dict = {"signal_type": SignalType.ANALOG}
_H = ("horizontal",)
_VU = ("vertical", "up")
_VD = ("vertical", "down")


class NPN(CircuitElement):
    """NPN bipolar transistor."""

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_NPN_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _BJT_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "base", direction=PinDirection.IN, routing_hints=_H, **_PIN_KWARGS,
        )
        self._register_pin(
            "collector", direction=PinDirection.INOUT, routing_hints=_VU, **_PIN_KWARGS,
        )
        self._register_pin(
            "emitter", direction=PinDirection.INOUT, routing_hints=_VD, **_PIN_KWARGS,
        )


class PNP(CircuitElement):
    """PNP bipolar transistor."""

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_PNP_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _BJT_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "base", direction=PinDirection.IN, routing_hints=_H, **_PIN_KWARGS,
        )
        self._register_pin(
            "collector", direction=PinDirection.INOUT, routing_hints=_VD, **_PIN_KWARGS,
        )
        self._register_pin(
            "emitter", direction=PinDirection.INOUT, routing_hints=_VU, **_PIN_KWARGS,
        )
