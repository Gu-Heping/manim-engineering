"""Teaching scene style overrides (durations, pulse widths, dim opacity)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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
EmphasisLevel = Literal["context", "normal", "key"]


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
    setup_caption_hold_scale: float = 1.15
    setup_post_hold: float = 0.12
    conclusion_caption_hold_scale: float = 1.3
    conclusion_post_hold: float = 0.28
    context_duration_scale: float = 0.85
    context_gap_scale: float = 0.85
    context_pulse_scale: float = 0.85
    key_duration_scale: float = 1.2
    key_gap_scale: float = 1.2
    key_pulse_scale: float = 1.15


def style_for_emphasis(
    style: TeachingStyle,
    emphasis: EmphasisLevel | None,
) -> TeachingStyle:
    """Return an emphasis-adjusted view of ``style`` without mutating defaults."""

    if emphasis is None or emphasis == "normal":
        return style
    if emphasis == "context":
        duration_scale = style.context_duration_scale
        gap_scale = style.context_gap_scale
        pulse_scale = style.context_pulse_scale
    else:
        duration_scale = style.key_duration_scale
        gap_scale = style.key_gap_scale
        pulse_scale = style.key_pulse_scale
    return TeachingStyle(
        beat_duration=style.beat_duration * duration_scale,
        beat_gap=style.beat_gap * gap_scale,
        caption_crossfade=style.caption_crossfade,
        dim_opacity=style.dim_opacity,
        pulse_flash_width=style.pulse_flash_width * pulse_scale,
        wire_flash_width=style.wire_flash_width * pulse_scale,
        waveform_flash_width=style.waveform_flash_width * pulse_scale,
        overlay_fade_out=style.overlay_fade_out,
        setup_caption_hold_scale=style.setup_caption_hold_scale,
        setup_post_hold=style.setup_post_hold,
        conclusion_caption_hold_scale=style.conclusion_caption_hold_scale,
        conclusion_post_hold=style.conclusion_post_hold,
        context_duration_scale=style.context_duration_scale,
        context_gap_scale=style.context_gap_scale,
        context_pulse_scale=style.context_pulse_scale,
        key_duration_scale=style.key_duration_scale,
        key_gap_scale=style.key_gap_scale,
        key_pulse_scale=style.key_pulse_scale,
    )
