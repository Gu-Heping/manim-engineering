"""P-channel MOSFET symbol stub.

Scope A (symbol-only): no continuous physics. Same pin layout as
:class:`~manim_engineering.components.analog.nmos.NMOS`; the renderer
distinguishes the two by drawing an inversion bubble at the gate of a
PMOS and reversing the channel-arrow direction.

PMOS conducts when ``gate`` is LOW (complementary to NMOS), which is what
the CMOS-inverter example demonstrates — but enforcement of that semantics
belongs to Scope B's continuous-physics propagation, not this symbol stub.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_PMOS_BOUNDS = Bounds(width=1.0, height=1.0)
_PMOS_ANCHORS: dict[str, AnchorPoint] = {
    "gate": (0.0, 0.5),
    "drain": (1.0, 0.0),
    "source": (1.0, 1.0),
    "center": (0.5, 0.5),
}


class PMOS(CircuitElement):
    """P-channel MOSFET. Channel conducts when ``gate`` is LOW.

    Pin layout is intentionally identical to NMOS (gate left, source/drain
    on the right column); the renderer adds the inversion-bubble glyph at
    the gate. Source is drawn at the top, drain at the bottom, mirroring
    typical CMOS-inverter schematics where PMOS sits above NMOS.
    """

    semantic_type = "analog"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_PMOS_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _PMOS_BOUNDS

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
            routing_hints=("vertical", "down"),
        )
        self._register_pin(
            "source",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "up"),
        )
