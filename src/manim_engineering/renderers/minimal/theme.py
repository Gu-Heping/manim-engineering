"""Minimal renderer theme: semantic colors and stroke hierarchy."""

from __future__ import annotations

from manim import BLUE_C, GREEN_C, GREY_C, ORANGE, RED_C, TEAL_C, YELLOW_C

from manim_engineering.semantic.connection import Connection
from manim_engineering.semantic.enums import SignalType

# Semantic colors (see docs/visual-theme.md)
POWER_COLOR = RED_C
GROUND_COLOR = GREY_C
CLOCK_COLOR = YELLOW_C
DATA_COLOR = GREEN_C
SIGNAL_COLOR = BLUE_C
ANALOG_COLOR = TEAL_C
WARNING_COLOR = ORANGE

# Preferred dark engineering backgrounds
BACKGROUND_COLORS: tuple[str, ...] = ("#1e1e2e", "#111111", "#202124")
DEFAULT_BACKGROUND = BACKGROUND_COLORS[0]

# Line width hierarchy
BUS_STROKE_WIDTH = 4.0
WIRE_STROKE_WIDTH = 2.5
HELPER_STROKE_WIDTH = 1.0

_COMPONENT_STROKE_WIDTH = WIRE_STROKE_WIDTH
_COMPONENT_COLOR = SIGNAL_COLOR

_SIGNAL_TYPE_COLORS: dict[SignalType, object] = {
    SignalType.POWER: POWER_COLOR,
    SignalType.GROUND: GROUND_COLOR,
    SignalType.CLOCK: CLOCK_COLOR,
    SignalType.DATA: DATA_COLOR,
    SignalType.SIGNAL: SIGNAL_COLOR,
    SignalType.DIGITAL: DATA_COLOR,
    SignalType.ANALOG: ANALOG_COLOR,
}


def color_for_signal_type(signal_type: SignalType) -> object:
    """Map engineering signal classification to theme stroke color."""
    return _SIGNAL_TYPE_COLORS.get(signal_type, SIGNAL_COLOR)


def color_for_connection(connection: Connection) -> object:
    """Pick wire color from connection endpoints (deterministic: lexicographic pin id)."""
    first, second = sorted(
        (connection.pin_a, connection.pin_b),
        key=lambda pin: pin.id,
    )
    for pin in (first, second):
        if pin.signal_type != SignalType.SIGNAL:
            return color_for_signal_type(pin.signal_type)
    return color_for_signal_type(first.signal_type)


def component_stroke_color() -> object:
    """Default stroke for passive / generic symbols."""
    return _COMPONENT_COLOR


def component_stroke_width() -> float:
    """Default stroke width for component symbols."""
    return _COMPONENT_STROKE_WIDTH
