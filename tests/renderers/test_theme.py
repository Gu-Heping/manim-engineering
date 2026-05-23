"""Theme constants map semantic kinds to Manim colors."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import BLUE_C, GREEN_C, ORANGE, RED_C, TEAL_C, YELLOW_C

from manim_engineering.core.enums import SignalType
from manim_engineering.renderers.minimal import theme


def test_semantic_color_constants_match_visual_theme_doc() -> None:
    assert theme.POWER_COLOR == RED_C
    # GROUND lives off the default GREY_C to stay legible on dark backgrounds.
    assert isinstance(theme.GROUND_COLOR, str)
    assert theme.GROUND_COLOR.startswith("#")
    assert theme.CLOCK_COLOR == YELLOW_C
    assert theme.DATA_COLOR == GREEN_C
    assert theme.SIGNAL_COLOR == BLUE_C
    assert theme.ANALOG_COLOR == TEAL_C
    assert theme.WARNING_COLOR == ORANGE


def test_digital_color_distinct_from_data() -> None:
    """Multi-line digital buses (e.g. SPI) must not share color with DATA."""
    # DATA is a ManimColor; DIGITAL is BLUE_C (also ManimColor) — compare repr
    # to avoid the ManimColor != ManimColor type collision quirk.
    assert repr(theme.DIGITAL_COLOR) != repr(theme.DATA_COLOR)
    assert theme.color_for_signal_type(SignalType.DIGITAL) == theme.DIGITAL_COLOR


def test_background_tokens_not_in_renderer_theme() -> None:
    """Background/highlight/muted live in ``animation.theme`` now; renderer

    only owns semantic stroke colours. Asserting absence here so accidental
    re-introductions get caught."""
    for name in ("DEFAULT_BACKGROUND", "BACKGROUND_COLORS", "HIGHLIGHT_COLOR", "MUTED_COLOR"):
        assert not hasattr(theme, name), (
            f"renderers/minimal/theme.py must not own {name!r} — "
            "scene-level tokens belong to animation/theme.py."
        )


def test_stroke_width_hierarchy() -> None:
    assert theme.BUS_STROKE_WIDTH > theme.WIRE_STROKE_WIDTH > theme.HELPER_STROKE_WIDTH


def test_color_for_signal_type_mapping() -> None:
    assert theme.color_for_signal_type(SignalType.POWER) == theme.POWER_COLOR
    assert theme.color_for_signal_type(SignalType.GROUND) == theme.GROUND_COLOR
    assert theme.color_for_signal_type(SignalType.CLOCK) == theme.CLOCK_COLOR
    assert theme.color_for_signal_type(SignalType.DATA) == theme.DATA_COLOR
    assert theme.color_for_signal_type(SignalType.SIGNAL) == theme.SIGNAL_COLOR
