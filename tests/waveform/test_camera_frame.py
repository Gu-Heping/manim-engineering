"""Camera framing must not use skewed VMobject bounding boxes."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from examples.protocol.spi_byte_transfer import SPI_SUBTITLE_BAND
from examples.protocol.spi_byte_transfer import build_spi_fixture as build_fixture

from manim_engineering.animation.pacing import subtitle_text
from manim_engineering.animation.scene import resolve_scene_camera
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.waveform import (
    camera_frame_center,
    frame_size_for_pixel_aspect,
    hud_text_y,
)
from manim_engineering.waveform.layout import step_polyline


def test_time_scale_fits_traces_in_panel_width() -> None:
    _, _, layout, _, _, bundle = build_fixture()
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
    _, _, layout, _, _, bundle = build_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    from manim_engineering.waveform import scene_frame_bounds

    _, fh = scene_frame_bounds(layout, spec, trace_count=4, target_fill=0.70)
    _, cy = camera_frame_center(layout, spec, trace_count=4)
    top = cy + fh / 2
    bottom = cy - fh / 2
    title_y = hud_text_y(cy, fh, row=0)
    assert bottom <= title_y <= top


def test_camera_center_near_circuit_not_waveform_bbox() -> None:
    _, _, layout, _, _, bundle = build_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    cx, cy = camera_frame_center(layout, spec, trace_count=len(bundle.traces))
    assert 0.0 <= cx <= layout.scene_bbox.max_x + 0.5
    assert cy < layout.scene_bbox.max_y + 1.0


def _hud_bottom(text_mob, baseline_y: float) -> float:
    """Approximate world-Y of the text bottom edge (Manim ``Text`` centres at move_to)."""
    height = float(text_mob.height)
    return baseline_y - height * 0.5


def _hud_top(text_mob, baseline_y: float) -> float:
    height = float(text_mob.height)
    return baseline_y + height * 0.5


def test_subtitle_title_and_caption_fit_inside_camera_frame() -> None:
    """Both HUD rows must land between frame top and bottom — no off-screen captions."""
    _, _, layout, _, _, bundle = build_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout,
        spec,
        bundle,
        pixel_width=1280,
        pixel_height=720,
        subtitle_band=SPI_SUBTITLE_BAND,
    )
    top = camera.frame_cy + camera.frame_height / 2
    bottom = camera.frame_cy - camera.frame_height / 2

    title = subtitle_text("SPI Mode 0 · TX 0xA5  RX 0x3C", role="title")
    caption = subtitle_text("① CS↓ 片选有效", role="caption")
    title_y = hud_text_y(camera.frame_cy, camera.frame_height, row=0)
    caption_y = hud_text_y(camera.frame_cy, camera.frame_height, row=1)

    assert bottom <= _hud_bottom(title, title_y)
    assert _hud_top(title, title_y) <= top
    assert bottom <= _hud_bottom(caption, caption_y)
    assert _hud_top(caption, caption_y) <= top
    assert _hud_bottom(title, title_y) > _hud_top(caption, caption_y)


def test_hud_text_y_caption_row_clears_circuit_top() -> None:
    """Caption row must not overlap the topology bounding box."""
    _, _, layout, _, _, bundle = build_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout,
        spec,
        bundle,
        pixel_width=1280,
        pixel_height=720,
        subtitle_band=SPI_SUBTITLE_BAND,
    )
    caption_y = hud_text_y(camera.frame_cy, camera.frame_height, row=1)
    caption = subtitle_text("① CS↓ 片选有效", role="caption")
    assert _hud_bottom(caption, caption_y) >= layout.scene_bbox.max_y - 0.05
