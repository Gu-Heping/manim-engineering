"""End-to-end camera/aspect invariants (inline fixture)."""

from __future__ import annotations

import pytest

from manim_engineering.animation.scene import resolve_scene_camera
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_rising_edge
from manim_engineering.waveform import derive_bundle_from_signals


def _build_minimal_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    graph.add(r1)
    graph.add(r2)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(graph, elements)
    sig = Signal(
        name="sig", signal_type=SignalType.SIGNAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    record_rising_edge(sig, r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((sig,))
    return graph, elements, layout, sig, bundle


def _pixel_aspect_targets() -> list[tuple[int, int]]:
    return [(1280, 720), (1920, 1080), (854, 480)]


@pytest.mark.parametrize("pixel_width,pixel_height", _pixel_aspect_targets())
def test_resolve_scene_camera_matches_pixel_aspect(pixel_width: int, pixel_height: int) -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout, spec, bundle,
        pixel_width=pixel_width, pixel_height=pixel_height,
    )
    target_aspect = pixel_width / pixel_height
    actual_aspect = camera.frame_width / camera.frame_height
    assert actual_aspect == pytest.approx(target_aspect, rel=1e-6)


def test_subtitle_band_shifts_center_up_by_half() -> None:
    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    base = resolve_scene_camera(layout, spec, bundle, pixel_width=1280, pixel_height=720)
    band = 0.9
    with_band = resolve_scene_camera(
        layout, spec, bundle,
        pixel_width=1280, pixel_height=720,
        subtitle_band=band,
    )
    assert with_band.frame_cy == pytest.approx(base.frame_cy + band / 2, rel=1e-6)
    assert with_band.frame_height >= base.frame_height


def test_scene_frame_bounds_contains_panel_bottom() -> None:
    from manim_engineering.waveform import scene_frame_bounds
    from manim_engineering.waveform.layout import panel_height

    _, _, layout, _, bundle = _build_minimal_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    _, fh = scene_frame_bounds(layout, spec, trace_count=len(bundle.traces))
    panel_bottom_world = spec.origin.y - panel_height(
        len(bundle.traces), spec.trace_height, spec.trace_gap,
    )
    content_height = layout.scene_bbox.max_y - panel_bottom_world
    assert fh >= content_height
