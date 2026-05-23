"""Minimal renderer: simple symbols and semantic theme colors."""

from manim_engineering.renderers.minimal.immutable import (
    TopologyProjection,
    copy_for_animation,
    topology_from_render,
)
from manim_engineering.renderers.minimal.manim_renderer import ManimRenderer
from manim_engineering.renderers.minimal.renderer import MinimalRenderer
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
from manim_engineering.renderers.minimal.waveform import WaveformPanelRenderer

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
    "ManimRenderer",
    "MinimalRenderer",
    "POWER_COLOR",
    "SIGNAL_COLOR",
    "TopologyProjection",
    "WARNING_COLOR",
    "WAVEFORM_LABEL_FONT_SIZE",
    "WAVEFORM_STROKE_WIDTH",
    "WIRE_STROKE_WIDTH",
    "WaveformPanelRenderer",
    "color_for_connection",
    "color_for_signal_type",
    "component_stroke_color",
    "component_stroke_width",
    "copy_for_animation",
    "topology_from_render",
]
