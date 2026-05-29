"""WaveformRevealTracker incremental edge reveal."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import VGroup

from manim_engineering.animation.waveform_reveal import (
    UnknownWaveformSignalError,
    WaveformRevealTracker,
    mount_reveal_plan,
)
from manim_engineering.core.enums import SignalType
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicState, Signal
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


def test_append_through_beat_returns_create_ready_segments() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()
    from manim_engineering.semantic import LogicLevel as LL
    from manim_engineering.semantic import LogicState, Signal

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LL.LOW))
    panel = VGroup(renderer.render_trace(trace, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()

    plan = tracker.append_through_beat(clk, 0)
    mount_reveal_plan(plan)
    assert plan.added
    assert all(float(line.get_stroke_opacity()) == pytest.approx(0.0) for line in plan.added)  # type: ignore[attr-defined]


def test_append_through_beat_preserves_unchanged_prefix_ids() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()
    from manim_engineering.semantic import LogicLevel as LL
    from manim_engineering.semantic import LogicState, Signal

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LL.LOW))
    panel = VGroup(renderer.render_trace(trace, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()
    prefix_ids = [id(mob) for mob in panel.submobjects[0].submobjects[:-1]]

    plan0 = tracker.append_through_beat(clk, 0)
    mount_reveal_plan(plan0)
    after_beat0 = list(panel.submobjects[0].submobjects[:-1])
    assert after_beat0
    assert id(after_beat0[0]) == prefix_ids[0]

    plan1 = tracker.append_through_beat(clk, 1)
    mount_reveal_plan(plan1)
    lines_after = list(panel.submobjects[0].submobjects[:-1])
    assert len(lines_after) > len(prefix_ids)
    assert id(lines_after[0]) == prefix_ids[0]


def test_append_through_time_rebuilds_hold_on_beat_advance() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()
    from manim_engineering.semantic import LogicLevel as LL
    from manim_engineering.semantic import LogicState, Signal

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LL.LOW))
    panel = VGroup(renderer.render_trace(trace, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()

    mount_reveal_plan(tracker.append_through_beat(clk, 0))
    lines_after_beat0 = list(tracker.panel.submobjects[0].submobjects[:-1])
    assert lines_after_beat0

    for plan in tracker.append_through_time(2.0):
        mount_reveal_plan(plan)
    lines_after_t2 = list(tracker.panel.submobjects[0].submobjects[:-1])
    assert len(lines_after_t2) >= len(lines_after_beat0)
    hold_end = max(
        max(line.get_start()[0], line.get_end()[0]) for line in lines_after_t2  # type: ignore[attr-defined]
    )
    assert hold_end == 2.0


def test_append_through_time_for_only_updates_named_trace() -> None:
    from manim_engineering.layout.types import Point2D
    from manim_engineering.waveform.trace import WaveformBundle

    vin = WaveformTrace(
        signal_name="vin",
        signal_type=SignalType.DIGITAL,
        pin_id="drv.out",
        samples=(
            WaveformSample(time=0.0, level=LogicLevel.LOW),
            WaveformSample(time=0.0, level=LogicLevel.HIGH),
        ),
    )
    vc = WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=1.0, level=0.4),
            WaveformSample(time=2.0, level=0.7),
        ),
        is_discrete=False,
    )
    bundle = WaveformBundle(traces=(vin, vc))
    spec = WaveformPanelSpec(
        origin=Point2D(0.0, -2.0),
        width=4.0,
        trace_height=0.4,
        trace_gap=0.5,
        time_scale=1.0,
    )
    renderer = WaveformPanelRenderer()
    panel = VGroup(
        renderer.render_trace(vin, spec, 0, idle_only=True),
        renderer.render_trace(vc, spec, 1, idle_only=True),
    )
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()

    vin_before = len(panel.submobjects[0].submobjects) - 1
    vc_before = len(panel.submobjects[1].submobjects) - 1

    mount_reveal_plan(tracker.append_through_time_for("vc", 2.0))

    assert len(panel.submobjects[0].submobjects) - 1 == vin_before
    assert len(panel.submobjects[1].submobjects) - 1 > vc_before
    assert tracker.revealed_time_for("vc") == pytest.approx(2.0)


def test_append_through_time_for_unknown_signal_raises_typed_error() -> None:
    tracker, _trace, _bundle, _spec, _renderer = _panel_fixture()

    with pytest.raises(UnknownWaveformSignalError):
        tracker.append_through_time_for("missing", 1.0)


def test_finalize_hold_extends_short_idle_stub() -> None:
    from manim_engineering.layout.types import Point2D
    from manim_engineering.waveform.trace import WaveformBundle

    vc = WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=2.0, level=0.63),
            WaveformSample(time=5.0, level=0.99),
        ),
        is_discrete=False,
    )
    bundle = WaveformBundle(traces=(vc,))
    spec = WaveformPanelSpec(
        origin=Point2D(0.0, -2.0),
        width=4.0,
        trace_height=0.4,
        trace_gap=0.5,
        time_scale=1.0,
    )
    renderer = WaveformPanelRenderer()
    panel = VGroup(renderer.render_trace(vc, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()

    pending = tracker.finalize_hold_to_panel()
    lines = list(panel.submobjects[0].submobjects[:-1])
    hold_end = max(max(line.get_start()[0], line.get_end()[0]) for line in lines)  # type: ignore[attr-defined]
    assert hold_end == pytest.approx(spec.origin.x + spec.width)
    assert pending == () or all(
        float(line.get_stroke_opacity()) == pytest.approx(0.0) for line in pending  # type: ignore[attr-defined]
    )


def test_mount_reveal_plan_adds_lines_without_label_placeholder() -> None:
    tracker, trace, bundle, spec, renderer = _panel_fixture()

    clk = Signal(
        name="clk",
        signal_type=SignalType.CLOCK,
        value=LogicState(level=LogicLevel.LOW),
    )
    trace_row = renderer.render_trace(trace, spec, 0, idle_only=True)
    bare_row = VGroup(*tracker._line_children(trace_row))
    panel = VGroup(bare_row)
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()

    plan = tracker.append_through_beat(clk, 0)
    mount_reveal_plan(plan)

    assert plan.added
    assert all(line in bare_row.submobjects for line in plan.added)


def test_finalize_hold_extends_partial_reveal_to_panel_edge() -> None:
    from manim_engineering.layout.types import Point2D
    from manim_engineering.waveform.trace import WaveformBundle

    vc = WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=2.0, level=0.63),
            WaveformSample(time=5.0, level=0.99),
        ),
        is_discrete=False,
    )
    bundle = WaveformBundle(traces=(vc,))
    spec = WaveformPanelSpec(
        origin=Point2D(0.0, -2.0),
        width=4.0,
        trace_height=0.4,
        trace_gap=0.5,
        time_scale=1.0,
    )
    renderer = WaveformPanelRenderer()
    panel = VGroup(renderer.render_trace(vc, spec, 0, idle_only=True))
    tracker = WaveformRevealTracker(panel, bundle, spec, renderer)
    tracker.sync_idle_baselines()
    mount_reveal_plan(tracker.append_through_time_for("vc", 2.0))

    pending = tracker.finalize_hold_to_panel()
    lines = list(panel.submobjects[0].submobjects[:-1])
    hold_end = max(max(line.get_start()[0], line.get_end()[0]) for line in lines)  # type: ignore[attr-defined]
    assert hold_end == pytest.approx(spec.origin.x + spec.width)
    assert pending == () or all(
        float(line.get_stroke_opacity()) == pytest.approx(0.0) for line in pending  # type: ignore[attr-defined]
    )
