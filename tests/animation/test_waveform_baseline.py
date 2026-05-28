"""Per-trace idle baseline filtering for teaching scenes."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import VGroup

from manim_engineering.animation.scene_template import _iter_trace_line_strokes_for_traces
from manim_engineering.core.enums import SignalType
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformSample, WaveformTrace


def test_baseline_trace_filter_excludes_unlisted_signals() -> None:
    from manim_engineering.layout.types import Point2D

    vin = WaveformTrace(
        signal_name="vin",
        signal_type=SignalType.DIGITAL,
        pin_id="drv.out",
        samples=(
            WaveformSample(time=0.0, level=LogicLevel.LOW),
            WaveformSample(time=1.0, level=LogicLevel.HIGH),
        ),
    )
    vc = WaveformTrace(
        signal_name="vc",
        signal_type=SignalType.ANALOG,
        pin_id="c1.a",
        samples=(
            WaveformSample(time=0.0, level=0.0),
            WaveformSample(time=2.0, level=0.5),
        ),
        is_discrete=False,
    )
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

    all_lines = _iter_trace_line_strokes_for_traces(panel, frozenset({0, 1}))
    vin_only = _iter_trace_line_strokes_for_traces(panel, frozenset({0}))

    assert len(all_lines) == 2
    assert len(vin_only) == 1
