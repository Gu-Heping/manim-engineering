"""Waveform layer: timing traces derived from signal state."""

from manim_engineering.waveform.derive import (
    derive_bundle_from_signals,
    derive_trace_from_signal,
    level_from_value,
    record_for_beat,
    timing_events_from_propagation,
)
from manim_engineering.waveform.layout import (
    WaveformPanelSpec,
    panel_below_layout,
    sample_to_point,
    step_polyline,
    transition_point_for_beat,
)
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace

__all__ = [
    "WaveformBundle",
    "WaveformPanelSpec",
    "WaveformSample",
    "WaveformTrace",
    "derive_bundle_from_signals",
    "derive_trace_from_signal",
    "level_from_value",
    "panel_below_layout",
    "record_for_beat",
    "sample_to_point",
    "step_polyline",
    "timing_events_from_propagation",
    "transition_point_for_beat",
]
