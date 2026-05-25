"""Topology-only camera helper tests (no waveform panel)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from manim_engineering.animation.scene import (
    TOPOLOGY_CAMERA_PADDING,
    configure_topology_scene_camera,
    resolve_topology_scene_camera,
)
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine


def _two_resistor_layout():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    return LayoutEngine().layout(graph, {"r1": r1, "r2": r2})


def test_resolve_topology_camera_fits_scene_bbox() -> None:
    """Frame width/height should comfortably exceed scene bbox + 2*padding."""
    layout = _two_resistor_layout()
    camera = resolve_topology_scene_camera(
        layout,
        pixel_width=1920,
        pixel_height=1080,
        target_fill=1.0,
        min_width=0.0,
        min_height=0.0,
        subtitle_band=0.0,
    )
    scene = layout.scene_bbox
    min_w = scene.width + 2 * TOPOLOGY_CAMERA_PADDING
    min_h = scene.height + 2 * TOPOLOGY_CAMERA_PADDING
    assert camera.frame_width >= min_w - 1e-9
    assert camera.frame_height >= min_h - 1e-9


@pytest.mark.parametrize("pixel_width,pixel_height", [(1280, 720), (1920, 1080), (854, 480)])
def test_resolve_topology_camera_respects_pixel_aspect(pixel_width: int, pixel_height: int) -> None:
    layout = _two_resistor_layout()
    camera = resolve_topology_scene_camera(
        layout,
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )
    target = pixel_width / pixel_height
    actual = camera.frame_width / camera.frame_height
    assert actual == pytest.approx(target, rel=1e-6)


def test_resolve_topology_camera_subtitle_band_shifts_center_up() -> None:
    layout = _two_resistor_layout()
    base = resolve_topology_scene_camera(layout, pixel_width=1280, pixel_height=720)
    band = 0.9
    with_band = resolve_topology_scene_camera(
        layout, pixel_width=1280, pixel_height=720, subtitle_band=band
    )
    assert with_band.frame_cy == pytest.approx(base.frame_cy + band / 2, rel=1e-6)
    assert with_band.frame_height >= base.frame_height


def test_resolve_topology_camera_invalid_target_fill_raises() -> None:
    layout = _two_resistor_layout()
    with pytest.raises(ValueError):
        resolve_topology_scene_camera(
            layout,
            pixel_width=1920,
            pixel_height=1080,
            target_fill=0.0,
        )
    with pytest.raises(ValueError):
        resolve_topology_scene_camera(
            layout,
            pixel_width=1920,
            pixel_height=1080,
            target_fill=1.5,
        )


@dataclass
class _StubCamera:
    frame_width: float = 0.0
    frame_height: float = 0.0
    frame_center: list[float] = field(default_factory=lambda: [0.0, 0.0])
    background_color: str = ""


@dataclass
class _StubScene:
    camera: _StubCamera = field(default_factory=_StubCamera)


def test_configure_topology_camera_mutates_scene_camera(monkeypatch: Any) -> None:
    """Helper writes frame_width/height/center and background onto the scene."""
    layout = _two_resistor_layout()
    scene = _StubScene()

    class _Cfg:
        pixel_width = 1920
        pixel_height = 1080

    def _fake_import():
        return _Cfg

    monkeypatch.setattr("manim.config", _Cfg, raising=False)
    camera = configure_topology_scene_camera(
        scene,
        layout,
        subtitle_band=0.9,
        apply_background=True,
        background_color="#123456",
    )

    assert scene.camera.frame_width == camera.frame_width
    assert scene.camera.frame_height == camera.frame_height
    assert scene.camera.frame_center == [camera.frame_cx, camera.frame_cy]
    assert scene.camera.background_color == "#123456"
    # Sanity: aspect respects 1920x1080.
    assert camera.frame_width / camera.frame_height == pytest.approx(16 / 9, rel=1e-6)


def test_configure_topology_camera_skips_background_when_disabled(
    monkeypatch: Any,
) -> None:
    layout = _two_resistor_layout()
    scene = _StubScene()
    scene.camera.background_color = "preserved"

    class _Cfg:
        pixel_width = 1280
        pixel_height = 720

    monkeypatch.setattr("manim.config", _Cfg, raising=False)

    configure_topology_scene_camera(scene, layout, apply_background=False)
    assert scene.camera.background_color == "preserved"
