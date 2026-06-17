"""IEC renderer theme surface.

The first IEC slice reuses minimal renderer geometry and semantic colors while
exposing a separate renderer-owned theme module. Future IEC symbol work should
extend here instead of styling semantic objects.
"""

from __future__ import annotations

from manim_engineering.renderers.minimal.theme import (
    ANALOG_COLOR,
    BUS_STROKE_WIDTH,
    CLOCK_COLOR,
    COMPONENT_LABEL_FONT_SIZE,
    DATA_COLOR,
    DIGITAL_COLOR,
    GROUND_COLOR,
    HELPER_STROKE_WIDTH,
    INTERFACE_PIN_FONT_SIZE,
    INTERFACE_ROLE_FONT_SIZE,
    POWER_COLOR,
    SIGNAL_COLOR,
    WARNING_COLOR,
    WAVEFORM_LABEL_FONT_SIZE,
    WAVEFORM_STROKE_WIDTH,
    WIRE_STROKE_WIDTH,
    color_for_connection,
    color_for_signal_type,
    component_stroke_color,
    component_stroke_width,
)

__all__ = [
    "ANALOG_COLOR",
    "BUS_STROKE_WIDTH",
    "CLOCK_COLOR",
    "COMPONENT_LABEL_FONT_SIZE",
    "DATA_COLOR",
    "DIGITAL_COLOR",
    "GROUND_COLOR",
    "HELPER_STROKE_WIDTH",
    "INTERFACE_PIN_FONT_SIZE",
    "INTERFACE_ROLE_FONT_SIZE",
    "POWER_COLOR",
    "SIGNAL_COLOR",
    "WARNING_COLOR",
    "WAVEFORM_LABEL_FONT_SIZE",
    "WAVEFORM_STROKE_WIDTH",
    "WIRE_STROKE_WIDTH",
    "color_for_connection",
    "color_for_signal_type",
    "component_stroke_color",
    "component_stroke_width",
]
