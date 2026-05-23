"""End-to-end camera/aspect invariants for the shared scene helper."""

from __future__ import annotations

import pytest
from examples.protocol.spi_byte_transfer import build_spi_fixture as spi_fixture

from manim_engineering.animation.scene import resolve_scene_camera
from manim_engineering.renderers.minimal import WaveformPanelRenderer


def _pixel_aspect_targets() -> list[tuple[int, int]]:
    return [(1280, 720), (1920, 1080), (854, 480)]


@pytest.mark.parametrize("pixel_width,pixel_height", _pixel_aspect_targets())
def test_resolve_scene_camera_matches_pixel_aspect(pixel_width: int, pixel_height: int) -> None:
    _, _, layout, _, _, bundle = spi_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    camera = resolve_scene_camera(
        layout,
        spec,
        bundle,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )
    target_aspect = pixel_width / pixel_height
    actual_aspect = camera.frame_width / camera.frame_height
    assert actual_aspect == pytest.approx(target_aspect, rel=1e-6)


def test_subtitle_band_shifts_center_up_by_half() -> None:
    _, _, layout, _, _, bundle = spi_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    base = resolve_scene_camera(
        layout,
        spec,
        bundle,
        pixel_width=1280,
        pixel_height=720,
    )
    band = 0.9
    with_band = resolve_scene_camera(
        layout,
        spec,
        bundle,
        pixel_width=1280,
        pixel_height=720,
        subtitle_band=band,
    )
    assert with_band.frame_cy == pytest.approx(base.frame_cy + band / 2, rel=1e-6)
    assert with_band.frame_height >= base.frame_height


def test_scene_frame_bounds_contains_panel_bottom() -> None:
    """Height must extend down to the bottom of the waveform panel."""
    from manim_engineering.waveform import scene_frame_bounds
    from manim_engineering.waveform.layout import panel_height

    _, _, layout, _, _, bundle = spi_fixture()
    spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    _, fh = scene_frame_bounds(layout, spec, trace_count=len(bundle.traces))

    panel_bottom_world = spec.origin.y - panel_height(
        len(bundle.traces),
        spec.trace_height,
        spec.trace_gap,
    )
    content_height = layout.scene_bbox.max_y - panel_bottom_world
    assert fh >= content_height
