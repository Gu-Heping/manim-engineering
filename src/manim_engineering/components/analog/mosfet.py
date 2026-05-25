"""Shared MOSFET footprint metadata (four-terminal, textbook-vertical default)."""

from __future__ import annotations

from typing import Literal

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

ConductionMode = Literal["enhancement", "depletion"]
ChannelPolarity = Literal["n", "p"]

MOSFET_BOUNDS = Bounds(width=1.0, height=1.0)
MOSFET_CHANNEL_X = 0.42
MOSFET_DRAIN_STUB_X = 1.0
MOSFET_SOURCE_STUB_X = 0.86

# Branch centres aligned with the three equal enhancement channel bars.
_CHANNEL_INSET = 0.08
_CHANNEL_SPAN = 1.0 - 2.0 * _CHANNEL_INSET
_SEGMENT_GAP = 0.10
_BAR = (_CHANNEL_SPAN - 2.0 * _SEGMENT_GAP * _CHANNEL_SPAN) / 3.0
Y_CHANNEL_TOP = _CHANNEL_INSET + _BAR * 0.5
Y_CHANNEL_MID = _CHANNEL_INSET + _BAR + _SEGMENT_GAP * _CHANNEL_SPAN + _BAR * 0.5
Y_CHANNEL_BOT = _CHANNEL_INSET + 2.0 * _BAR + 2.0 * _SEGMENT_GAP * _CHANNEL_SPAN + _BAR * 0.5

NMOS_ANCHORS: dict[str, AnchorPoint] = {
    "gate": (0.0, 0.5),
    "drain": (MOSFET_DRAIN_STUB_X, 1.0),
    "source": (MOSFET_SOURCE_STUB_X, 0.0),
    "bulk": (MOSFET_SOURCE_STUB_X, Y_CHANNEL_TOP),
    "center": (0.5, 0.5),
}

PMOS_ANCHORS: dict[str, AnchorPoint] = {
    "gate": (0.0, 0.5),
    "drain": (MOSFET_DRAIN_STUB_X, 0.0),
    "source": (MOSFET_SOURCE_STUB_X, 1.0),
    "bulk": (MOSFET_SOURCE_STUB_X, Y_CHANNEL_BOT),
    "center": (0.5, 0.5),
}


def register_mosfet_pins(component: CircuitElement, *, p_channel: bool) -> None:
    """Register gate/drain/source/bulk for textbook-vertical MOSFET symbols."""
    component._register_pin(
        "gate",
        direction=PinDirection.IN,
        signal_type=SignalType.ANALOG,
        routing_hints=("horizontal",),
    )
    if p_channel:
        component._register_pin(
            "drain",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "down"),
        )
        component._register_pin(
            "source",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "up"),
        )
    else:
        component._register_pin(
            "drain",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "up"),
        )
        component._register_pin(
            "source",
            direction=PinDirection.INOUT,
            signal_type=SignalType.ANALOG,
            routing_hints=("vertical", "down"),
        )
    component._register_pin(
        "bulk",
        direction=PinDirection.IN,
        signal_type=SignalType.ANALOG,
        routing_hints=("horizontal",),
    )
