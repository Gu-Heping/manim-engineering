"""RC teaching scene camera framing invariants."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.animation.scene import resolve_scene_camera
from manim_engineering.renderers.minimal import WaveformPanelRenderer

pytest.importorskip("manim")

REPO = Path(__file__).resolve().parents[2]
_RC_SUBTITLE_BAND = 1.25
_MIN_TOPOLOGY_FRAME_RATIO = 0.18


def _load_rc_module():
    spec = importlib.util.spec_from_file_location(
        "rc_charge",
        REPO / "examples/analog/01_rc_charge.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rc_teaching_camera(*, target_fill: float):
    mod = _load_rc_module()
    graph, elements, layout, signals, bundle, records = mod.build_rc_teaching_fixture()
    del graph, elements, signals, records
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return resolve_scene_camera(
        layout,
        panel_spec,
        bundle,
        pixel_width=1280,
        pixel_height=720,
        subtitle_band=_RC_SUBTITLE_BAND,
        target_fill=target_fill,
    ), layout


def test_rc_topology_height_ratio_with_default_fill() -> None:
    camera, layout = _rc_teaching_camera(target_fill=0.70)
    scene = layout.scene_bbox
    topo_h = scene.max_y - scene.min_y
    ratio = topo_h / camera.frame_height
    assert ratio >= _MIN_TOPOLOGY_FRAME_RATIO


def test_rc_topology_height_ratio_with_scene_target_fill() -> None:
    """RCChargeScene uses camera_target_fill=0.85 for larger on-screen symbols."""
    camera, layout = _rc_teaching_camera(target_fill=0.85)
    scene = layout.scene_bbox
    topo_h = scene.max_y - scene.min_y
    ratio = topo_h / camera.frame_height
    assert ratio >= _MIN_TOPOLOGY_FRAME_RATIO
    camera_default, _ = _rc_teaching_camera(target_fill=0.70)
    assert camera.frame_height <= camera_default.frame_height
