"""RCChargeScene intro pipeline and teaching beat smoke tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")
pytest.importorskip("PIL")

from manim import AnimationGroup, Create, DrawBorderThenFill, LaggedStart, Scene, VGroup

from manim_engineering.debug.snapshot import redraw_scene_frame

REPO = Path(__file__).resolve().parents[2]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_rc_module():
    return _load_module(REPO / "examples/analog/01_rc_charge.py")


def _contains_intro_reveal(animation: object) -> bool:
    if isinstance(animation, (Create, DrawBorderThenFill)):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_intro_reveal(child) for child in animation.animations)
    return False


def test_rc_charge_scene_class_available() -> None:
    mod = _load_rc_module()
    assert hasattr(mod, "RCChargeScene")
    assert issubclass(mod.RCChargeScene, Scene)


def test_rc_teaching_beats_disable_wire_pulse() -> None:
    mod = _load_rc_module()
    _, _, _, signals, _, records = mod.build_rc_teaching_fixture()
    beats = mod._teaching_beats(signals, records)
    assert len(beats) == 2
    assert beats[0].emphasis == "context"
    assert beats[1].emphasis == "key"
    assert beats[0].wire_pulse is False
    assert beats[1].wire_pulse is False


def test_play_topology_intro_exported_from_animation_package() -> None:
    from manim_engineering.animation import CaptionTrack, play_hud_intro, play_topology_intro

    assert callable(play_topology_intro)
    assert callable(play_hud_intro)
    assert CaptionTrack is not None


def test_rc_shared_reexports_teaching_scene_from_package() -> None:
    shared = _load_module(REPO / "examples/_shared.py")
    assert shared.WaveformDemoScene.__module__.startswith("manim_engineering.animation")
    assert shared.WaveformFixture.__module__.startswith("manim_engineering.animation")
    assert shared.CaptionTrack.__module__.startswith("manim_engineering.animation")


def test_rc_charge_scene_construct_smoke() -> None:
    mod = _load_rc_module()

    class _RecordingScene(mod.RCChargeScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            self._waited = 0
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

        def wait(self, duration: float = 0.0) -> None:
            del duration
            self._waited += 1

    scene = _RecordingScene()
    scene.construct()
    assert scene.played
    assert scene._waited > 0
    intro_anims, _ = scene.played[0]
    assert any(_contains_intro_reveal(anim) for anim in intro_anims)


def test_waveform_demo_scene_exposes_play_intro_hook() -> None:
    from manim_engineering.animation import WaveformDemoScene

    assert callable(WaveformDemoScene.play_intro)


def test_waveform_demo_scene_lives_in_animation_package() -> None:
    from manim_engineering.animation import WaveformDemoScene

    assert WaveformDemoScene.__module__.endswith("teaching_scene")


def test_waveform_demo_scene_default_hud_intro_is_title_only() -> None:
    mod = _load_rc_module()
    scene = mod.RCChargeScene()
    fixture = scene.build_fixture()
    title_text, _intro_text = scene.hud_texts(fixture)
    intro_title, intro_copy = scene.hud_intro_texts(fixture)
    assert intro_title in title_text
    assert "IN" not in intro_title
    assert "R1" not in intro_title
    assert "C1" not in intro_title
    assert "GND" not in intro_title
    assert intro_copy == ""


def test_rc_intro_annotations_reveal_waveform_trace_labels() -> None:
    mod = _load_rc_module()
    fixture = mod.RCChargeScene().build_fixture()

    from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
    from manim_engineering.renderers.minimal.labels import (
        detach_label_roots,
        hide_labels,
        iter_label_roots,
        label_visible,
    )

    topology = ManimRenderer().render_topology(
        fixture.graph,
        fixture.layout,
        dict(fixture.elements),
    )
    waveform_panel, _panel_spec = WaveformPanelRenderer().render_with_layout(
        fixture.bundle,
        fixture.layout,
        idle_only=True,
    )
    hide_labels(topology.components)
    hide_labels(waveform_panel)
    topology_labels = type(topology.components)(*detach_label_roots(topology.components))
    waveform_panel_labels = type(waveform_panel)(*detach_label_roots(waveform_panel))

    class _RecordingScene(mod.RCChargeScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

    scene = _RecordingScene()
    scene.play_intro_annotations(topology_labels, waveform_panel_labels)

    visible_waveform_labels = {
        label.text
        for label in iter_label_roots(VGroup(*scene.mobjects), roles=("waveform_label",))
        if label_visible(label)
    }
    assert visible_waveform_labels == {"vin", "vc"}


def test_rc_skip_baseline_restores_idle_stub_visibility() -> None:
    mod = _load_rc_module()
    fixture = mod.RCChargeScene().build_fixture()
    from manim_engineering.animation.waveform_controller import WaveformSegmentController
    from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
    from manim_engineering.renderers.minimal import WaveformPanelRenderer

    panel_renderer = WaveformPanelRenderer()
    waveform_panel, panel_spec = panel_renderer.render_with_layout(
        fixture.bundle,
        fixture.layout,
        idle_only=True,
    )
    tracker = WaveformRevealTracker(
        waveform_panel,
        fixture.bundle,
        panel_spec,
        panel_renderer,
    )
    controller = WaveformSegmentController(tracker)
    scene = mod.RCChargeScene()

    scene.play_waveform_baseline_intro(
        waveform_panel,
        controller,
        bundle=fixture.bundle,
    )

    trace_lines = [
        mob
        for trace_group in waveform_panel.submobjects[:-1]
        for mob in trace_group.submobjects[:-1]
        if mob.__class__.__name__ == "Line"
    ]
    assert trace_lines
    assert all(float(line.get_stroke_opacity()) == pytest.approx(1.0) for line in trace_lines)


def test_rc_intro_static_redraw_matches_live_frame() -> None:
    from PIL import ImageChops

    mod = _load_rc_module()

    class _ProbeScene(mod.RCChargeScene):
        def __init__(self) -> None:
            self.redraw_diff_bbox = None
            super().__init__()

        def construct(self) -> None:
            fixture = self.build_fixture()
            from manim_engineering.animation.scene import configure_waveform_scene_camera
            from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
            from manim_engineering.renderers.minimal.labels import detach_label_roots, hide_labels

            topology = ManimRenderer().render_topology(
                fixture.graph,
                fixture.layout,
                dict(fixture.elements),
            )
            waveform_panel, panel_spec = WaveformPanelRenderer().render_with_layout(
                fixture.bundle,
                fixture.layout,
                idle_only=True,
            )
            topology_labels = VGroup(*detach_label_roots(topology.components))
            waveform_panel_labels = VGroup(*detach_label_roots(waveform_panel))
            hide_labels(topology_labels)
            hide_labels(waveform_panel_labels)
            content = VGroup(topology.components, topology.wires, waveform_panel)

            configure_waveform_scene_camera(
                self,
                fixture.layout,
                panel_spec,
                fixture.bundle,
                target_fill=self.camera_target_fill,
                subtitle_band=0.0,
            )
            self.play_intro(topology, waveform_panel, content)
            before = self.camera.get_image().copy()
            redraw_scene_frame(self)
            after = self.camera.get_image().copy()
            self.redraw_diff_bbox = ImageChops.difference(before, after).getbbox()

    scene = _ProbeScene()
    scene.render()
    assert scene.redraw_diff_bbox is None


def test_rc_prebeat_static_redraw_matches_live_frame() -> None:
    from PIL import ImageChops

    mod = _load_rc_module()

    class _ProbeScene(mod.RCChargeScene):
        def __init__(self) -> None:
            self.redraw_diff_bbox = None
            super().__init__()

        def construct(self) -> None:
            fixture = self.build_fixture()
            from manim_engineering.animation.hud import play_hud_intro
            from manim_engineering.animation.scene import configure_waveform_scene_camera
            from manim_engineering.animation.teaching_scene import _refresh_static_scene_background
            from manim_engineering.animation.waveform_controller import WaveformSegmentController
            from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
            from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
            from manim_engineering.renderers.minimal.labels import detach_label_roots, hide_labels

            topology = ManimRenderer().render_topology(
                fixture.graph,
                fixture.layout,
                dict(fixture.elements),
            )
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(
                fixture.bundle,
                fixture.layout,
                idle_only=True,
            )
            reveal_tracker = WaveformRevealTracker(
                waveform_panel,
                fixture.bundle,
                panel_spec,
                panel_renderer,
            )
            waveform_controller = WaveformSegmentController(reveal_tracker)
            topology_labels = VGroup(*detach_label_roots(topology.components))
            waveform_panel_labels = VGroup(*detach_label_roots(waveform_panel))
            hide_labels(topology_labels)
            hide_labels(waveform_panel_labels)
            content = VGroup(topology.components, topology.wires, waveform_panel)

            camera = configure_waveform_scene_camera(
                self,
                fixture.layout,
                panel_spec,
                fixture.bundle,
                target_fill=self.camera_target_fill,
                subtitle_band=0.0,
            )
            self.play_intro(topology, waveform_panel, content)
            hud = self.hud_intro_texts(fixture)
            if hud is not None:
                play_hud_intro(self, hud[0], hud[1], camera)
            self.play_intro_annotations(topology_labels, waveform_panel_labels)
            self.after_intro_hook(fixture, camera)
            self.play_waveform_baseline_intro(
                waveform_panel,
                waveform_controller,
                bundle=fixture.bundle,
            )
            _refresh_static_scene_background(self)
            before = self.camera.get_image().copy()
            redraw_scene_frame(self)
            after = self.camera.get_image().copy()
            self.redraw_diff_bbox = ImageChops.difference(before, after).getbbox()

    scene = _ProbeScene()
    scene.render()
    assert scene.redraw_diff_bbox is None
