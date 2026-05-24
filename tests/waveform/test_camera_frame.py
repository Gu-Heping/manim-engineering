"""Camera framing invariants (inline fixture, no external examples)."""

from __future__ import annotations

import pytest

from manim_engineering.animation.pacing import subtitle_text
from manim_engineering.animation.scene import resolve_scene_camera
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_rising_edge
from manim_engineering.waveform import (
    camera_frame_center,
    derive_bundle_from_signals,
    frame_size_for_pixel_aspect,
    hud_text_y,
)
from manim_engineering.waveform.layout import step_polyline

pytest.importorskip("manim")

_SUBTITLE_BAND = 1.25


def _build_minimal_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    graph.add(r1)
    graph.add(r2)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(graph, elements)
    sig = Signal(name="sig", signal_type=SignalType.SIGNAL, value=LogicState(level=LogicLevel.LOW))
    record_rising_edge(sig, r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((sig,))
    return graph, elements, layout, sig, bundle


def test_time_scale_fits_traces_in_panel_width() -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    assert spec.time_scale > 0
    for index, trace in enumerate(bundle.traces):
        points = step_polyline(trace, spec, index)
        xs = [p.x for p in points]
        assert max(xs) <= spec.origin.x + spec.width + 0.01


def test_frame_size_matches_16_9_pixel_aspect() -> None:
    w, h = frame_size_for_pixel_aspect(5.0, 5.0, pixel_width=1280, pixel_height=720)
    assert w / h == pytest.approx(1280 / 720, rel=1e-6)
    assert w > 5.0


def test_hud_text_y_inside_frame_top() -> None:
    from manim_engineering.waveform import scene_frame_bounds

    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    _, fh = scene_frame_bounds(layout, spec, trace_count=1, target_fill=0.70)
    _, cy = camera_frame_center(layout, spec, trace_count=1)
    top = cy + fh / 2
    bottom = cy - fh / 2
    title_y = hud_text_y(cy, fh, row=0)
    assert bottom <= title_y <= top


def test_camera_center_near_circuit_not_waveform_bbox() -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    cx, cy = camera_frame_center(layout, spec, trace_count=len(bundle.traces))
    assert 0.0 <= cx <= layout.scene_bbox.max_x + 0.5
    assert cy < layout.scene_bbox.max_y + 1.0


def _hud_bottom(text_mob, baseline_y: float) -> float:
    return baseline_y - float(text_mob.height) * 0.5


def _hud_top(text_mob, baseline_y: float) -> float:
    return baseline_y + float(text_mob.height) * 0.5


def test_subtitle_title_and_caption_fit_inside_camera_frame() -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout, spec, bundle, pixel_width=1280, pixel_height=720, subtitle_band=_SUBTITLE_BAND,
    )
    top = camera.frame_cy + camera.frame_height / 2
    bottom = camera.frame_cy - camera.frame_height / 2
    title = subtitle_text("Test Title", role="title")
    caption = subtitle_text("Test Caption", role="caption")
    title_y = hud_text_y(camera.frame_cy, camera.frame_height, row=0)
    caption_y = hud_text_y(camera.frame_cy, camera.frame_height, row=1)
    assert bottom <= _hud_bottom(title, title_y)
    assert _hud_top(title, title_y) <= top
    assert bottom <= _hud_bottom(caption, caption_y)
    assert _hud_top(caption, caption_y) <= top
    assert _hud_bottom(title, title_y) > _hud_top(caption, caption_y)


def test_hud_text_y_caption_row_clears_circuit_top() -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout, spec, bundle, pixel_width=1280, pixel_height=720, subtitle_band=_SUBTITLE_BAND,
    )
    caption_y = hud_text_y(camera.frame_cy, camera.frame_height, row=1)
    caption = subtitle_text("Test Caption", role="caption")
    assert _hud_bottom(caption, caption_y) >= layout.scene_bbox.max_y - 0.05
