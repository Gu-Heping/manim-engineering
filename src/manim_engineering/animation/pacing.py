"""Shared scene pacing constants (seconds) and HUD font/subtitle helpers.

Kept in the animation layer because pacing and on-screen captions belong to
the same authoring contract: a beat reads a caption, a beat plays motion,
a gap holds the frame. Centralising fonts here prevents every example from
hard-coding ``font="Microsoft YaHei"`` and prevents subtitle styling from
drifting across SPI/UART/clock_data scenes.
"""

from __future__ import annotations

import os

INTRO_PAUSE = 1.8
BEAT_DURATION = 1.2
BEAT_GAP = 0.5
OUTRO_PAUSE = 1.5

# Reading pause after a caption fades in, *before* the matching motion plays.
# 3B1B convention: "let the eye catch up with the text". Without this, the
# caption + pulse fire in the same instant and the viewer cannot read either.
BEAT_CAPTION_HOLD = 0.4

# Length of the final FadeOut(*self.mobjects) transition that closes a scene
# cleanly instead of cutting on a held frame. Subtracted from ``OUTRO_PAUSE``.
SCENE_FADE_OUT = 0.8

# Soft landing when removing propagation/timing overlays between beats.
OVERLAY_FADE_OUT = 0.15

# HUD caption crossfade (intro → beat captions).
CAPTION_CROSSFADE = 0.45

# Ordered CJK font fallback. The first available font wins; the trailing
# ``sans-serif`` is the Manim/cairo system fallback for ASCII glyphs.
CJK_FONT_STACK: tuple[str, ...] = (
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "PingFang SC",
    "Source Han Sans SC",
    "sans-serif",
)

# 3B1B HUD typography: prominent white title, muted intro / caption.
# Sizes follow the SKILL.md guide (title ~36–44 on a 1080p canvas).
SUBTITLE_TITLE_FONT_SIZE = 36
SUBTITLE_CAPTION_FONT_SIZE = 26
SUBTITLE_INTRO_FONT_SIZE = 24

SUBTITLE_TITLE_COLOR = "#FFFFFF"
SUBTITLE_INTRO_COLOR = "#BDBDBD"  # matches theme.MUTED_COLOR (GREY_B)
SUBTITLE_CAPTION_COLOR = "#DDDDDD"  # GREY_A — softer than pure white


def scene_final_fade_enabled() -> bool:
    """Return ``False`` when ``ME_SUPPRESS_FADE=1``.

    Visual golden tests render with ``save_last_frame=True`` and need the
    pre-fade content frame, not an empty post-fade frame. CLI renders keep
    the FadeOut so videos end gracefully.
    """
    return os.environ.get("ME_SUPPRESS_FADE") != "1"


def _pick_font(stack: tuple[str, ...]) -> str:
    """First entry of the font stack (Manim resolves its own system fallback)."""
    return stack[0] if stack else "sans-serif"


def subtitle_text(
    label: str,
    *,
    role: str = "caption",
    font_stack: tuple[str, ...] = CJK_FONT_STACK,
):
    """Return a configured ``manim.Text`` for HUD titles, intros, or captions.

    ``role`` is one of ``"title" | "intro" | "caption"`` and controls font size
    and color. Import is lazy so the helper can be imported in non-Manim
    contexts.
    """
    from manim import Text

    if role == "title":
        font_size = SUBTITLE_TITLE_FONT_SIZE
        color = SUBTITLE_TITLE_COLOR
    elif role == "intro":
        font_size = SUBTITLE_INTRO_FONT_SIZE
        color = SUBTITLE_INTRO_COLOR
    elif role == "caption":
        font_size = SUBTITLE_CAPTION_FONT_SIZE
        color = SUBTITLE_CAPTION_COLOR
    else:
        msg = f"unknown subtitle role: {role!r}"
        raise ValueError(msg)

    return Text(
        label,
        font_size=font_size,
        color=color,
        font=_pick_font(font_stack),
    )
