"""TopologyTeachingScene intro/HUD smoke (no waveform panel)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import ImageChops

pytest.importorskip("manim")
pytest.importorskip("PIL")

from manim import AnimationGroup, Create, DrawBorderThenFill, LaggedStart

from manim_engineering.animation.teaching_scene import (
    TopologyFixture,
    TopologyTeachingScene,
    _refresh_static_scene_background,
)
from manim_engineering.components import Diode, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine

REPO = Path(__file__).resolve().parents[2]


def _rectifier_fixture() -> TopologyFixture:
    graph = CircuitGraph()
    src = InputDriver("src", label="AC", signal_type=SignalType.ANALOG)
    d1 = Diode("d1", label="D1")
    rl = Resistor("rl", label="RL")
    gnd = Ground("gnd", label="GND")
    for comp in (src, d1, rl, gnd):
        comp.attach_to(graph)
    graph.connect(src.get_pin("out"), d1.get_pin("anode"))
    graph.connect(d1.get_pin("cathode"), rl.get_pin("a"))
    graph.connect(rl.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"src": src, "d1": d1, "rl": rl, "gnd": gnd}
    layout = LayoutEngine().solve(graph, elements)
    return TopologyFixture(graph=graph, elements=elements, layout=layout)


def _contains_intro_reveal(animation: object) -> bool:
    if isinstance(animation, (Create, DrawBorderThenFill)):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_intro_reveal(child) for child in animation.animations)
    return False


def test_topology_teaching_scene_construct_smoke() -> None:
    class _RectifierScene(TopologyTeachingScene):
        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            return _rectifier_fixture()

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return ("半波整流 路 AC→D1→RL→GND", "交流源→二极管→负载")

    class _RecordingScene(_RectifierScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

        def wait(self, duration: float = 0.0) -> None:
            del duration

    scene = _RecordingScene()
    scene.construct()
    assert scene.played
    intro_anims, _ = scene.played[0]
    assert any(_contains_intro_reveal(anim) for anim in intro_anims)


def test_topology_teaching_scene_does_not_set_components_opacity() -> None:
    fixture = _rectifier_fixture()

    class _Scene(TopologyTeachingScene):
        def build_fixture(self) -> TopologyFixture:
            return fixture

    scene = _Scene()
    topology = scene.render_topology(fixture)
    with patch.object(scene, "render_topology", return_value=topology):
        with patch.object(topology.components, "set_opacity") as comp_opacity:
            scene.construct()
    comp_opacity.assert_not_called()


def test_half_wave_rectifier_example_exports_topology_scene() -> None:
    spec = importlib.util.spec_from_file_location(
        "diode_rectifier",
        REPO / "examples/analog/02_diode_rectifier.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.HalfWaveRectifierScene is not None
    assert issubclass(mod.HalfWaveRectifierScene, TopologyTeachingScene)


def test_topology_teaching_scene_default_hud_intro_is_title_only() -> None:
    class _RectifierScene(TopologyTeachingScene):
        def build_fixture(self) -> TopologyFixture:
            return _rectifier_fixture()

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return ("半波整流 路 AC→D1→RL→GND", "交流源→二极管→负载")

    scene = _RectifierScene()
    fixture = scene.build_fixture()
    title_text, _intro_text = scene.hud_texts(fixture)
    intro_title, intro_copy = scene.hud_intro_texts(fixture)
    assert intro_title == title_text.split(" 路 ", 1)[0]
    assert intro_copy == ""


def test_topology_teaching_scene_prehold_redraw_matches_live_frame() -> None:
    class _RectifierScene(TopologyTeachingScene):
        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            return _rectifier_fixture()

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return ("半波整流 路 AC→D1→RL→GND", "交流源→二极管→负载")

    class _ProbeScene(_RectifierScene):
        def __init__(self) -> None:
            self.redraw_diff_bbox = None
            super().__init__()

        def construct(self) -> None:
            fixture = self.build_fixture()
            from manim import VGroup

            from manim_engineering.animation.hud import play_hud_intro
            from manim_engineering.animation.scene import configure_topology_scene_camera
            from manim_engineering.renderers.minimal.labels import detach_label_roots, hide_labels

            hud = self.hud_intro_texts(fixture)
            topology = self.render_topology(fixture)
            topology_labels = VGroup(*detach_label_roots(topology.components))
            hide_labels(topology_labels)
            empty_panel = VGroup()
            content = VGroup(topology.components, topology.wires)

            camera = configure_topology_scene_camera(
                self,
                fixture.layout,
                target_fill=self.camera_target_fill,
                subtitle_band=self.subtitle_band,
            )

            self.play_intro(topology, empty_panel, content)
            if hud is not None:
                play_hud_intro(self, hud[0], hud[1], camera)
            self.play_intro_annotations(topology_labels, empty_panel)
            self.after_intro_hook(fixture, camera)
            _refresh_static_scene_background(self)
            before = self.camera.get_image().copy()
            from manim_engineering.debug.snapshot import redraw_scene_frame

            redraw_scene_frame(self)
            after = self.camera.get_image().copy()
            self.redraw_diff_bbox = ImageChops.difference(before, after).getbbox()

    scene = _ProbeScene()
    scene.render()
    assert scene.redraw_diff_bbox is None
