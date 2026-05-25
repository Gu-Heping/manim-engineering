"""Operational amplifier symbol stub.

Scope A (symbol-only): three signal pins (``in_p``, ``in_n``, ``out``) and
no rails. The renderer draws the canonical equilateral triangle pointing
right with ``+`` / ``-`` glyphs inside. Adding ``vcc`` / ``vee`` supply
pins is reserved for Scope A v2; nothing in the current example library
needs them.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_OPAMP_BOUNDS = Bounds(width=1.2, height=1.0)
_OPAMP_ANCHORS: dict[str, AnchorPoint] = {
    "in_p": (0.0, 0.75),
    "in_n": (0.0, 0.25),
    "out": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class OpAmp(CircuitElement):
    """Operational amplifier with ``in_p`` (+), ``in_n`` (−), and ``out``.

    Without rails, ``out`` is purely an ideal abstraction (Scope A). For
    examples that need a sensible saturation level, drive ``out`` through
    an analog signal explicitly.
    """

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_OPAMP_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _OPAMP_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "in_p",
            direction=PinDirection.IN,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
        self._register_pin(
            "in_n",
            direction=PinDirection.IN,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
        self._register_pin(
            "out",
            direction=PinDirection.OUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
