"""Teaching scene style overrides (durations, pulse widths, dim opacity)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.animation.focus import DEFAULT_DIM_OPACITY
from manim_engineering.animation.pacing import (
    BEAT_DURATION,
    BEAT_GAP,
    CAPTION_CROSSFADE,
    OVERLAY_FADE_OUT,
)

DEFAULT_PULSE_FLASH_WIDTH = 0.55
DEFAULT_WIRE_FLASH_WIDTH = 0.35
DEFAULT_WAVEFORM_FLASH_WIDTH = 0.65


@dataclass(frozen=True)
class TeachingStyle:
    """Scene- or beat-level animation tuning without forking orchestration code."""

    beat_duration: float = BEAT_DURATION
    beat_gap: float = BEAT_GAP
    caption_crossfade: float = CAPTION_CROSSFADE
    dim_opacity: float = DEFAULT_DIM_OPACITY
    pulse_flash_width: float = DEFAULT_PULSE_FLASH_WIDTH
    wire_flash_width: float = DEFAULT_WIRE_FLASH_WIDTH
    waveform_flash_width: float = DEFAULT_WAVEFORM_FLASH_WIDTH
    overlay_fade_out: float = OVERLAY_FADE_OUT
