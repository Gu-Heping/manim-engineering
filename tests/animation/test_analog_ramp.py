"""AnalogRamp primitive contract."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.animation import BEAT_DURATION, AnalogRamp
from manim_engineering.core.enums import SignalType
from manim_engineering.layout.types import Point2D
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformSample, WaveformTrace


def _trace() -> WaveformTrace:
    return WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=1.0, level=0.5),
            WaveformSample(time=2.0, level=0.86),
        ),
        is_discrete=False,
    )


def test_analog_ramp_builds_flash_plan() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    ramp = AnalogRamp(_trace(), panel_spec=spec, trace_index=0, t_end=2.0, duration=BEAT_DURATION)
    plan = ramp.build()
    assert plan.run_time == BEAT_DURATION
    assert plan.propagation_overlays
    assert plan.animations


def test_analog_ramp_aligns_with_signal_flow_duration() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    ramp = AnalogRamp(_trace(), panel_spec=spec, trace_index=0, t_end=1.0, duration=BEAT_DURATION)
    assert ramp.aligns_with_signal_flow(BEAT_DURATION)


def test_analog_ramp_clips_segment_when_t_start_positive() -> None:
    from manim_engineering.animation.analog_ramp import segment_points_for_time_range

    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    trace = _trace()
    full = segment_points_for_time_range(trace, spec, 0, t_start=0.0, t_end=2.0)
    partial = segment_points_for_time_range(trace, spec, 0, t_start=1.0, t_end=2.0)
    assert len(full) >= 2
    assert len(partial) >= 2
    assert partial[0].x >= spec.origin.x + 1.0 * spec.time_scale - 1e-6
