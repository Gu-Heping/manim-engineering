"""Diode symbol stub.

Scope A (symbol-only): no IV-curve / forward-drop physics. ``anode``→
``cathode`` direction is encoded by pin :class:`PinDirection`; the
renderer draws the triangle pointing from anode to cathode with the
cathode bar.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_DIODE_BOUNDS = Bounds(width=0.8, height=0.4)
_DIODE_ANCHORS: dict[str, AnchorPoint] = {
    "anode": (0.0, 0.5),
    "cathode": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class Diode(CircuitElement):
    """One-way analog conductor with ``anode`` (IN) and ``cathode`` (OUT)."""

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_DIODE_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _DIODE_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "anode",
            direction=PinDirection.IN,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
        self._register_pin(
            "cathode",
            direction=PinDirection.OUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
