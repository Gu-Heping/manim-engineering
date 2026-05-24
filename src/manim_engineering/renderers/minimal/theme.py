"""Minimal renderer theme: renderer-owned semantic colours and stroke hierarchy.

Scope: colours and strokes that this renderer assigns to *semantic concepts*
(POWER / GROUND / CLOCK / DATA / DIGITAL / ANALOG / SIGNAL / WARNING) plus
line widths, pulse sizing, and component font sizes.

Out of scope: scene-level visual decisions (background colour, transient
emphasis halo, secondary HUD copy). Those live in ``animation/theme.py``
and are shared across every renderer variant.
"""

from __future__ import annotations

from manim import BLUE_C, GREEN_C, ORANGE, RED_C, TEAL_C, WHITE, YELLOW_C

from manim_engineering.core.connection import Connection
from manim_engineering.core.enums import SignalType

# Semantic colors (see docs/visual-theme.md). DIGITAL and DATA must read as
# different traces on a shared bus (e.g. SPI CS vs MOSI/MISO), so DIGITAL
# uses BLUE_C while DATA stays GREEN_C. GROUND_COLOR is lifted off GREY_C to
# a brighter near-white-grey for legibility on dark backgrounds.
POWER_COLOR = RED_C
GROUND_COLOR = "#9A9AAB"
CLOCK_COLOR = YELLOW_C
DATA_COLOR = GREEN_C
SIGNAL_COLOR = BLUE_C
DIGITAL_COLOR = BLUE_C
ANALOG_COLOR = TEAL_C
WARNING_COLOR = ORANGE

# Line width hierarchy
BUS_STROKE_WIDTH = 4.0
WIRE_STROKE_WIDTH = 2.5
WAVEFORM_STROKE_WIDTH = 3.25
HELPER_STROKE_WIDTH = 1.0

# Symbol proportions (relative to component bounds)
RESISTOR_ZIGZAG_AMPLITUDE = 0.35
CAPACITOR_PLATE_GAP = 0.15
MOSFET_ARROW_SIZE = 0.12
PMOS_GATE_BUBBLE_RADIUS = 0.07
GND_BAR_TOP = 0.40
GND_BAR_MID = 0.28
GND_BAR_BOT = 0.18
COMPONENT_LABEL_Y_OFFSET = 0.12
VCC_LABEL_FONT_SIZE = 16
VCC_LABEL_OFFSET = 0.08
JUNCTION_DOT_RADIUS = 0.045

# Propagation pulse (SignalFlow overlay)
PULSE_RADIUS_MIN = 0.09
PULSE_RADIUS_MAX = 0.18
PULSE_RADIUS_WIRE_RATIO = 0.12
PULSE_TRAIL_STROKE_WIDTH = 2.0
PULSE_TRAIL_OPACITY = 0.35

# Text font sizes in Manim CE points (same convention as animation/pacing HUD:
# SUBTITLE_TITLE 36, CAPTION 26). Do not use fractional "world unit" values here.
COMPONENT_LABEL_FONT_SIZE = 20
WAVEFORM_LABEL_FONT_SIZE = 22
INTERFACE_ROLE_FONT_SIZE = 28
INTERFACE_PIN_FONT_SIZE = 18

_COMPONENT_STROKE_WIDTH = 3.75
# SPI/UART device outline only — thinner than passives so low-res frames stay hollow.
_INTERFACE_BOX_STROKE_WIDTH = 1.25
# Must match animation.theme.DEFAULT_BACKGROUND ("#1e1e2e"); not imported to avoid layer coupling.
INTERFACE_PANEL_FILL = "#1e1e2e"
_PIN_DOT_RADIUS = 0.035
_COMPONENT_COLOR = WHITE

_SIGNAL_TYPE_COLORS: dict[SignalType, object] = {
    SignalType.POWER: POWER_COLOR,
    SignalType.GROUND: GROUND_COLOR,
    SignalType.CLOCK: CLOCK_COLOR,
    SignalType.DATA: DATA_COLOR,
    SignalType.SIGNAL: SIGNAL_COLOR,
    SignalType.DIGITAL: DIGITAL_COLOR,
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


def interface_box_stroke_width() -> float:
    """Stroke width for protocol interface outlines (MCU/SLV boxes)."""
    return _INTERFACE_BOX_STROKE_WIDTH


def interface_box_stroke_color() -> object:
    """Softer outline than pure white — reduces colored-label halo at box edges."""
    return GROUND_COLOR


def pin_dot_radius() -> float:
    """Radius for terminal markers at anchor points."""
    return _PIN_DOT_RADIUS


def pulse_radius_for_wire_length(wire_length: float) -> float:
    """Scale pulse dot from routed path length (clamped)."""
    scaled = wire_length * PULSE_RADIUS_WIRE_RATIO
    return max(PULSE_RADIUS_MIN, min(PULSE_RADIUS_MAX, scaled))
