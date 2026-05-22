"""Minimal renderer: simple symbols and semantic theme colors."""

from manim_engineering.renderers.minimal.renderer import MinimalRenderer
from manim_engineering.renderers.minimal.theme import (
    ANALOG_COLOR,
    BACKGROUND_COLORS,
    BUS_STROKE_WIDTH,
    CLOCK_COLOR,
    DATA_COLOR,
    DEFAULT_BACKGROUND,
    GROUND_COLOR,
    HELPER_STROKE_WIDTH,
    POWER_COLOR,
    SIGNAL_COLOR,
    WARNING_COLOR,
    WIRE_STROKE_WIDTH,
    color_for_connection,
    color_for_signal_type,
    component_stroke_color,
    component_stroke_width,
)
from manim_engineering.renderers.minimal.waveform import WaveformPanelRenderer

__all__ = [
    "ANALOG_COLOR",
    "BACKGROUND_COLORS",
    "BUS_STROKE_WIDTH",
    "CLOCK_COLOR",
    "DATA_COLOR",
    "DEFAULT_BACKGROUND",
    "GROUND_COLOR",
    "HELPER_STROKE_WIDTH",
    "MinimalRenderer",
    "WaveformPanelRenderer",
    "POWER_COLOR",
    "SIGNAL_COLOR",
    "WARNING_COLOR",
    "WIRE_STROKE_WIDTH",
    "color_for_connection",
    "color_for_signal_type",
    "component_stroke_color",
    "component_stroke_width",
]
