"""Progressive reveal: step_polyline max_beat truncation."""

from __future__ import annotations

from manim_engineering.waveform.layout import WaveformPanelSpec, step_polyline
from manim_engineering.waveform.trace import WaveformTrace
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.core.enums import SignalType


def _trace() -> WaveformTrace:
    from manim_engineering.waveform.trace import WaveformSample

    return WaveformTrace(
        signal_name="clk",
        signal_type=SignalType.CLOCK,
        pin_id="r1.b",
        samples=(
            WaveformSample(time=0.0, level=LogicLevel.LOW),
            WaveformSample(time=1.0, level=LogicLevel.HIGH),
            WaveformSample(time=2.0, level=LogicLevel.LOW),
            WaveformSample(time=3.0, level=LogicLevel.HIGH),
        ),
    )


def test_step_polyline_idle_only_is_flat() -> None:
    spec = WaveformPanelSpec(origin=_origin(), width=4.0, trace_height=0.4, trace_gap=0.5)
    pts = step_polyline(_trace(), spec, 0, idle_only=True)
    ys = {p.y for p in pts}
    assert len(ys) == 1


def test_step_polyline_max_beat_grows_with_edges() -> None:
    spec = WaveformPanelSpec(origin=_origin(), width=4.0, trace_height=0.4, trace_gap=0.5)
    trace = _trace()
    idle = step_polyline(trace, spec, 0, idle_only=True)
    beat0 = step_polyline(trace, spec, 0, max_beat=0)
    beat1 = step_polyline(trace, spec, 0, max_beat=1)
    full = step_polyline(trace, spec, 0, max_beat=None)
    assert len(beat0) > len(idle)
    assert len(beat1) > len(beat0)
    assert len(full) >= len(beat1)


def _origin():
    from manim_engineering.layout.types import Point2D

    return Point2D(0.0, -2.0)
