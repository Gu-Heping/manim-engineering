"""N-channel MOSFET symbol stub.

Scope A (symbol-only): no continuous physics. ``gate``, ``drain``, ``source``
are all ``SignalType.ANALOG``; signal propagation between them still uses the
digital edge engine in ``manim_engineering.semantic.propagation`` — see
ROADMAP backlog for the continuous-physics upgrade path.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_NMOS_BOUNDS = Bounds(width=1.0, height=1.0)
_NMOS_ANCHORS: dict[str, AnchorPoint] = {
    "gate": (0.0, 0.5),
    "drain": (1.0, 1.0),
    "source": (1.0, 0.0),
    "center": (0.5, 0.5),
}


class NMOS(CircuitElement):
    """N-channel MOSFET. Channel conducts when ``gate`` is HIGH.

    Pin layout (renderer draws gate on the left, drain on top-right, source
    on bottom-right; arrow points *into* the channel — N-type convention).
    """

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_NMOS_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _NMOS_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin(
            "gate",
            direction=PinDirection.IN,
            signal_type=SignalType.ANALOG,
            routing_hints=("horizontal",),
        )
        self._register_pin(
            "drain",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "up"),
        )
        self._register_pin(
            "source",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "down"),
        )
