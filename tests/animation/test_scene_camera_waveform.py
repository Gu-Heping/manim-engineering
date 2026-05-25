"""Waveform-aware camera helper tests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from manim_engineering.animation.scene import configure_waveform_scene_camera
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals


def _waveform_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="clk",
        signal_type=SignalType.CLOCK,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((signal,))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return layout, bundle, panel_spec


@dataclass
class _StubCamera:
    frame_width: float = 0.0
    frame_height: float = 0.0
    frame_center: list[float] = field(default_factory=lambda: [0.0, 0.0])
    background_color: str = ""


@dataclass
class _StubScene:
    camera: _StubCamera = field(default_factory=_StubCamera)


def test_configure_waveform_camera_mutates_scene_camera(monkeypatch: Any) -> None:
    layout, bundle, panel_spec = _waveform_fixture()
    scene = _StubScene()

    class _Cfg:
        pixel_width = 1920
        pixel_height = 1080

    monkeypatch.setattr("manim.config", _Cfg, raising=False)
    camera = configure_waveform_scene_camera(
        scene,
        layout,
        panel_spec,
        bundle,
        subtitle_band=1.0,
        apply_background=True,
        background_color="#1e1e2e",
    )

    assert scene.camera.frame_width == camera.frame_width
    assert scene.camera.frame_height == camera.frame_height
    assert scene.camera.frame_center == [camera.frame_cx, camera.frame_cy]
    assert scene.camera.background_color == "#1e1e2e"
    assert camera.frame_width / camera.frame_height == pytest.approx(16 / 9, rel=1e-6)
