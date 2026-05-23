"""Waveform layer: timing traces derived from signal state."""

from manim_engineering.waveform.derive import (
    derive_bundle_from_signals,
    derive_trace_from_signal,
    level_from_value,
    record_for_beat,
    timing_events_from_propagation,
)
from manim_engineering.waveform.layout import (
    MIN_WAVEFORM_GAP,
    WaveformPanelSpec,
    camera_frame_center,
    frame_size_for_pixel_aspect,
    hud_text_y,
    panel_below_layout,
    sample_to_point,
    scene_frame_bounds,
    step_polyline,
    time_scale_for_bundle,
    transition_point_for_beat,
)
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace

__all__ = [
    "MIN_WAVEFORM_GAP",
    "WaveformBundle",
    "WaveformPanelSpec",
    "WaveformSample",
    "WaveformTrace",
    "camera_frame_center",
    "derive_bundle_from_signals",
    "derive_trace_from_signal",
    "frame_size_for_pixel_aspect",
    "hud_text_y",
    "level_from_value",
    "panel_below_layout",
    "record_for_beat",
    "sample_to_point",
    "scene_frame_bounds",
    "step_polyline",
    "time_scale_for_bundle",
    "timing_events_from_propagation",
    "transition_point_for_beat",
]
