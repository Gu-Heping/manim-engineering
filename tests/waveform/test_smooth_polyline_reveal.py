"""Progressive reveal: smooth_polyline hold_through_time truncation."""

from __future__ import annotations

import pytest

from manim_engineering.core.enums import SignalType
from manim_engineering.layout.types import Point2D
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.waveform.layout import (
    WaveformPanelSpec,
    _interpolate_sample_at_time,
    smooth_polyline,
)
from manim_engineering.waveform.trace import WaveformSample, WaveformTrace


def _analog_trace() -> WaveformTrace:
    return WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=1.0, level=0.4),
            WaveformSample(time=2.0, level=0.7),
            WaveformSample(time=3.0, level=0.9),
        ),
        is_discrete=False,
    )


def test_smooth_polyline_idle_only_is_flat() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    pts = smooth_polyline(_analog_trace(), spec, 0, idle_only=True)
    ys = {p.y for p in pts}
    assert len(ys) == 1


def test_smooth_polyline_hold_through_time_grows() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    trace = _analog_trace()
    partial = smooth_polyline(trace, spec, 0, hold_through_time=1.0, extend_to_panel=False)
    full = smooth_polyline(trace, spec, 0, hold_through_time=3.0, extend_to_panel=False)
    assert partial[-1].x <= full[-1].x
    assert len(full) >= len(partial)


def test_smooth_polyline_connects_samples_directly() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    pts = smooth_polyline(_analog_trace(), spec, 0, extend_to_panel=False)
    assert len(pts) >= 4


def test_smooth_polyline_hold_before_first_sample_is_monotonic_in_x() -> None:
    spec = WaveformPanelSpec(origin=Point2D(0.0, -2.0), width=4.0, trace_height=0.4, trace_gap=0.5)
    trace = WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=1.0, level=0.0),
            WaveformSample(time=2.0, level=0.5),
            WaveformSample(time=3.0, level=0.9),
        ),
        is_discrete=False,
    )
    pts = smooth_polyline(trace, spec, 0, hold_through_time=0.5, extend_to_panel=False)
    xs = [point.x for point in pts]
    assert xs == sorted(xs)


def test_interpolate_sample_holds_digital_level_before_transition() -> None:
    samples = (
        WaveformSample(time=0.0, level=LogicLevel.LOW),
        WaveformSample(time=1.0, level=LogicLevel.HIGH),
    )
    result = _interpolate_sample_at_time(samples, 0.5)
    assert result.time == pytest.approx(0.5)
    assert result.level == LogicLevel.LOW
