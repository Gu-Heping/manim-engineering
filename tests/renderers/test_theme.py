"""Theme constants map semantic kinds to Manim colors."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import BLUE_C, GREEN_C, GREY_C, ORANGE, RED_C, TEAL_C, YELLOW_C

from manim_engineering.renderers.minimal import theme
from manim_engineering.semantic.enums import SignalType


def test_semantic_color_constants_match_visual_theme_doc() -> None:
    assert theme.POWER_COLOR == RED_C
    assert theme.GROUND_COLOR == GREY_C
    assert theme.CLOCK_COLOR == YELLOW_C
    assert theme.DATA_COLOR == GREEN_C
    assert theme.SIGNAL_COLOR == BLUE_C
    assert theme.ANALOG_COLOR == TEAL_C
    assert theme.WARNING_COLOR == ORANGE


def test_background_palette_non_empty() -> None:
    assert len(theme.BACKGROUND_COLORS) >= 1
    assert theme.DEFAULT_BACKGROUND in theme.BACKGROUND_COLORS
    assert all(color.startswith("#") for color in theme.BACKGROUND_COLORS)


def test_stroke_width_hierarchy() -> None:
    assert theme.BUS_STROKE_WIDTH > theme.WIRE_STROKE_WIDTH > theme.HELPER_STROKE_WIDTH


def test_color_for_signal_type_mapping() -> None:
    assert theme.color_for_signal_type(SignalType.POWER) == theme.POWER_COLOR
    assert theme.color_for_signal_type(SignalType.GROUND) == theme.GROUND_COLOR
    assert theme.color_for_signal_type(SignalType.CLOCK) == theme.CLOCK_COLOR
    assert theme.color_for_signal_type(SignalType.DATA) == theme.DATA_COLOR
    assert theme.color_for_signal_type(SignalType.SIGNAL) == theme.SIGNAL_COLOR
