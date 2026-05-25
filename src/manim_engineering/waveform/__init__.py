"""Waveform layer: timing traces derived from signal state."""

from manim_engineering.waveform.derive import (
    derive_bundle_from_signals,
    derive_trace_from_signal,
    level_from_value,
    record_for_beat,
    timing_events_from_propagation,
)
from manim_engineering.waveform.exceptions import InvalidWaveformParamsError
from manim_engineering.waveform.layout import (
    MIN_WAVEFORM_GAP,
    WaveformPanelSpec,
    beat_for_time,
    camera_frame_center,
    frame_size_for_pixel_aspect,
    hud_text_y,
    panel_below_layout,
    polyline_for_trace,
    sample_to_point,
    scene_frame_bounds,
    smooth_polyline,
    step_polyline,
    time_scale_for_bundle,
    transition_point_for_beat,
)
from manim_engineering.waveform.rc import (
    RCStepParams,
    derive_rc_waveform_bundle,
    rc_charge_level_normalized,
    rc_charge_samples,
    rc_charge_voltage,
)
from manim_engineering.waveform.spi import derive_spi_waveform_bundle
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace

__all__ = [
    "InvalidWaveformParamsError",
    "MIN_WAVEFORM_GAP",
    "WaveformBundle",
    "WaveformPanelSpec",
    "WaveformSample",
    "WaveformTrace",
    "beat_for_time",
    "camera_frame_center",
    "derive_bundle_from_signals",
    "derive_rc_waveform_bundle",
    "derive_spi_waveform_bundle",
    "derive_trace_from_signal",
    "frame_size_for_pixel_aspect",
    "hud_text_y",
    "level_from_value",
    "panel_below_layout",
    "polyline_for_trace",
    "record_for_beat",
    "rc_charge_level_normalized",
    "rc_charge_samples",
    "rc_charge_voltage",
    "RCStepParams",
    "sample_to_point",
    "scene_frame_bounds",
    "smooth_polyline",
    "step_polyline",
    "time_scale_for_bundle",
    "timing_events_from_propagation",
    "transition_point_for_beat",
]
