"""SPI teaching beats reveal clk/mosi/miso incrementally."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import VGroup

from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.layout.types import Point2D
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.waveform.layout import WaveformPanelSpec, beat_for_time, step_polyline

_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "protocol" / "spi_byte_transfer.py"


def _load_spi_module():
    spec = importlib.util.spec_from_file_location("spi_byte_transfer", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(_EXAMPLE.parents[1]))
    spec.loader.exec_module(mod)
    return mod


def _spi_tracker():
    mod = _load_spi_module()
    _graph, _elements, layout, _binding, _result, bundle = mod.build_spi_fixture()
    renderer = WaveformPanelRenderer()
    panel_spec = renderer.panel_spec_for_layout(layout, bundle)
    panel = renderer.render_bundle(bundle, panel_spec, idle_only=True)
    tracker = WaveformRevealTracker(panel, bundle, panel_spec, renderer)
    return tracker, bundle, panel_spec


def _line_children(trace_group: VGroup) -> list[object]:
    return list(trace_group.submobjects[:-1])


def _trace_end_x(trace_group: VGroup) -> float:
    lines = _line_children(trace_group)
    assert lines
    return max(max(line.get_start()[0], line.get_end()[0]) for line in lines)  # type: ignore[attr-defined]


def _expected_segment_count(trace, spec, trace_index, reveal_time: float) -> int:
    beat = beat_for_time(trace, reveal_time)
    points = step_polyline(
        trace,
        spec,
        trace_index,
        max_beat=beat,
        extend_to_panel=False,
        hold_through_time=reveal_time,
    )
    return sum(
        1
        for start, end in zip(points, points[1:], strict=False)
        if not (start.x == end.x and start.y == end.y)
    )


def test_spi_beats_use_shared_reveal_time() -> None:
    mod = _load_spi_module()
    _graph, _elements, _layout, binding, _result, _bundle = mod.build_spi_fixture()
    beats = mod._teaching_beats(binding)

    assert beats[0].reveal_time == 0.0
    assert beats[1].reveal_time == 0.0
    assert beats[2].reveal_time == 2.0
    assert beats[3].reveal_time == 4.0


def test_spi_traces_share_controller_time_axis() -> None:
    mod = _load_spi_module()
    _graph, _elements, _layout, _binding, _result, bundle = mod.build_spi_fixture()
    clk = bundle.trace_named("clk")
    cs = bundle.trace_named("cs")
    assert clk is not None and cs is not None
    assert clk.samples[1].time == 0.0
    assert cs.samples[-2].time == 0.0


def test_spi_reveal_time_aligns_trace_right_edges() -> None:
    tracker, bundle, _spec = _spi_tracker()
    for reveal_time in (2.0, 4.0, 8.0):
        tracker.append_through_time(reveal_time)
        end_x_values = [
            _trace_end_x(tracker.panel.submobjects[index])
            for index in range(len(bundle.traces))
        ]
        assert len(set(round(x, 6) for x in end_x_values)) == 1


def test_spi_reveal_segment_counts_match_polyline() -> None:
    tracker, bundle, spec = _spi_tracker()
    for reveal_time in (2.0, 4.0):
        tracker.append_through_time(reveal_time)
        for index, trace in enumerate(bundle.traces):
            trace_group = tracker.panel.submobjects[index]
            expected = _expected_segment_count(trace, spec, index, reveal_time)
            assert len(_line_children(trace_group)) == expected


def test_spi_clk_hold_shortens_when_edges_advance() -> None:
    tracker, bundle, spec = _spi_tracker()
    clk_index = next(i for i, t in enumerate(bundle.traces) if t.signal_name == "clk")
    tracker.append_through_time(2.0)
    lines_t2 = _line_children(tracker.panel.submobjects[clk_index])
    assert len(lines_t2) >= 3
    third_end_t2 = max(lines_t2[2].get_start()[0], lines_t2[2].get_end()[0])  # type: ignore[attr-defined]

    tracker.append_through_time(4.0)
    lines_t4 = _line_children(tracker.panel.submobjects[clk_index])
    hold_end = max(
        max(line.get_start()[0], line.get_end()[0]) for line in lines_t4  # type: ignore[attr-defined]
    )

    beat = beat_for_time(bundle.traces[clk_index], 4.0)
    points = step_polyline(
        bundle.traces[clk_index],
        spec,
        clk_index,
        max_beat=beat,
        hold_through_time=4.0,
    )
    assert round(hold_end, 6) == round(points[-1].x, 6)
    assert third_end_t2 < hold_end
