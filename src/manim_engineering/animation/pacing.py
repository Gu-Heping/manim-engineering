"""Shared scene pacing constants (seconds) and HUD font/subtitle helpers.

Kept in the animation layer because pacing and on-screen captions belong to
the same authoring contract: a beat reads a caption, a beat plays motion,
a gap holds the frame.
"""

from __future__ import annotations

import os
import sys

INTRO_PAUSE = 1.8
BEAT_DURATION = 1.2
BEAT_GAP = 0.5
OUTRO_PAUSE = 1.5

BEAT_CAPTION_HOLD = 0.4
SCENE_FADE_OUT = 0.8
OVERLAY_FADE_OUT = 0.15
CAPTION_CROSSFADE = 0.45

SUBTITLE_TITLE_FONT_SIZE = 36
SUBTITLE_CAPTION_FONT_SIZE = 26
SUBTITLE_INTRO_FONT_SIZE = 24

SUBTITLE_TITLE_COLOR = "#FFFFFF"
SUBTITLE_INTRO_COLOR = "#BDBDBD"
SUBTITLE_CAPTION_COLOR = "#DDDDDD"

_PLATFORM_CJK: dict[str, str] = {
    "win32": "Microsoft YaHei",
    "darwin": "PingFang SC",
}


def _cjk_font() -> str:
    override = os.environ.get("ME_HUD_FONT")
    if override:
        return override
    return _PLATFORM_CJK.get(sys.platform, "Noto Sans CJK SC")


def scene_final_fade_enabled() -> bool:
    return os.environ.get("ME_SUPPRESS_FADE") != "1"


def subtitle_text(label: str, *, role: str = "caption"):
    """Return a configured ``manim.Text`` for HUD titles, intros, or captions.

    ``role`` is one of ``"title" | "intro" | "caption"``.
    """
    from manim import Text

    _sizes = {
        "title": (SUBTITLE_TITLE_FONT_SIZE, SUBTITLE_TITLE_COLOR),
        "intro": (SUBTITLE_INTRO_FONT_SIZE, SUBTITLE_INTRO_COLOR),
        "caption": (SUBTITLE_CAPTION_FONT_SIZE, SUBTITLE_CAPTION_COLOR),
    }
    entry = _sizes.get(role)
    if entry is None:
        msg = f"unknown subtitle role: {role!r}"
        raise ValueError(msg)
    font_size, color = entry
    return Text(label, font_size=font_size, color=color, font=_cjk_font())
