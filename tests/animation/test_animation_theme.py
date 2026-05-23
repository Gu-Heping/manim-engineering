"""Animation visual tokens (3B1B scene-level palette)."""

from __future__ import annotations

import re

from manim_engineering.animation import theme as anim_theme

_HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


def test_required_tokens_exist() -> None:
    """All four scene-level tokens are present so examples can ``from animation import ...``."""
    for name in ("DEFAULT_BACKGROUND", "BACKGROUND_COLORS", "HIGHLIGHT_COLOR", "MUTED_COLOR"):
        assert hasattr(anim_theme, name), f"animation/theme.py missing token {name!r}"


def test_tokens_are_valid_hex() -> None:
    assert _HEX_PATTERN.match(anim_theme.DEFAULT_BACKGROUND)
    assert _HEX_PATTERN.match(anim_theme.HIGHLIGHT_COLOR)
    assert _HEX_PATTERN.match(anim_theme.MUTED_COLOR)
    assert all(_HEX_PATTERN.match(c) for c in anim_theme.BACKGROUND_COLORS)


def test_default_background_in_palette() -> None:
    assert anim_theme.DEFAULT_BACKGROUND in anim_theme.BACKGROUND_COLORS


def test_default_background_is_3b1b_temperate_dark() -> None:
    """3B1B brief mandates ``#1e1e2e`` (warm dark) over pure black."""
    assert anim_theme.DEFAULT_BACKGROUND == "#1e1e2e"


def test_highlight_warm_gold_not_pure_yellow() -> None:
    """Halo must differ from ``CLOCK_COLOR`` (YELLOW_C) to avoid clashing."""
    assert anim_theme.HIGHLIGHT_COLOR == "#FFCB6B"


def test_tokens_re_exported_from_animation_package() -> None:
    """Examples import these from ``manim_engineering.animation`` directly."""
    from manim_engineering import animation

    assert animation.DEFAULT_BACKGROUND == anim_theme.DEFAULT_BACKGROUND
    assert animation.HIGHLIGHT_COLOR == anim_theme.HIGHLIGHT_COLOR
    assert animation.MUTED_COLOR == anim_theme.MUTED_COLOR
    assert animation.BACKGROUND_COLORS == anim_theme.BACKGROUND_COLORS
