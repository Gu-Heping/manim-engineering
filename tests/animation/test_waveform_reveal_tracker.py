"""WaveformRevealTracker incremental edge reveal."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import VGroup

from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.core.enums import SignalType
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformSample, WaveformTrace


def _panel_fixture():
    trace = WaveformTrace(
        signal_name="clk",
        signal_type=SignalType.CLOCK,
        pin_id="m.clk",
        samples=(
            WaveformSample(time=0.0, level=LogicLevel.LOW),
            WaveformSample(time=1.0, level=LogicLevel.HIGH),
            WaveformSample(time=2.0, level=LogicLevel.LOW),
            WaveformSample(time=3.0, level=LogicLevel.HIGH),
        ),
    )
    from manim_engineering.layout.types import Point2D
    from manim_engineering.waveform.trace import WaveformBundle

    bundle = WaveformBundle(traces=(trace,))
    spec = WaveformPanelSpec(
        origin=Point2D(0.0, -2.0),
        width=4.0,
        trace_height=0.4,
        trace_gap=0.5,
        time_scale=1.0,
    )
    renderer = WaveformPanelRenderer()
    trace_row = renderer.render_trace(trace, spec, 0, idle_only=True)
    panel = VGroup(trace_row)
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    return tracker, trace, bundle, spec, renderer


def test_append_through_beat_starts_new_segments_at_zero_width() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()
    from manim_engineering.semantic import LogicLevel as LL
    from manim_engineering.semantic import LogicState, Signal

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LL.LOW))
    panel = VGroup(renderer.render_trace(trace, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)

    added = tracker.append_through_beat(clk, 0)
    assert added
    assert all(line.get_stroke_width() == 0.0 for line in added)  # type: ignore[attr-defined]


def test_append_through_time_rebuilds_hold_on_beat_advance() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()
    from manim_engineering.semantic import LogicLevel as LL
    from manim_engineering.semantic import LogicState, Signal

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LL.LOW))
    panel = VGroup(renderer.render_trace(trace, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)

    tracker.append_through_beat(clk, 0)
    lines_after_beat0 = list(tracker.panel.submobjects[0].submobjects[:-1])
    assert lines_after_beat0

    tracker.append_through_time(2.0)
    lines_after_t2 = list(tracker.panel.submobjects[0].submobjects[:-1])
    assert len(lines_after_t2) >= len(lines_after_beat0)
    hold_end = max(
        max(line.get_start()[0], line.get_end()[0]) for line in lines_after_t2  # type: ignore[attr-defined]
    )
    assert hold_end == 2.0
