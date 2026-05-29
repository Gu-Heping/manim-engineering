"""CMOSInverterScene intro + teaching beat smoke tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from PIL import ImageChops

pytest.importorskip("manim")
pytest.importorskip("PIL")

from manim import AnimationGroup, Create, DrawBorderThenFill, LaggedStart, Scene, VGroup
from scene_trace import played_role_sets, scene_visible_label_texts

from manim_engineering.animation.label_phase import LabelPhasePolicy, label_allowed_in_phase
from manim_engineering.debug.snapshot import redraw_scene_frame
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.renderers.minimal.labels import (
    detach_label_roots,
    hide_labels,
    iter_label_roots,
    label_category,
    label_visible,
    refresh_label_strokes,
)

REPO = Path(__file__).resolve().parents[2]


def _load_cmos_module():
    spec = importlib.util.spec_from_file_location(
        "cmos_inverter",
        REPO / "examples/analog/03_cmos_inverter.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _contains_intro_reveal(animation: object) -> bool:
    if isinstance(animation, (Create, DrawBorderThenFill)):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_intro_reveal(child) for child in animation.animations)
    return False


def _label_visible(label: object) -> bool:
    return label_visible(label)


def test_cmos_scene_class_available() -> None:
    mod = _load_cmos_module()
    assert mod.CMOSInverterScene is not None
    assert issubclass(mod.CMOSInverterScene, Scene)


def test_cmos_teaching_beats_count() -> None:
    mod = _load_cmos_module()
    _, _, _, signals, _, records = mod.build_cmos_teaching_fixture()
    beats = mod._teaching_beats(signals, records)
    assert len(beats) == 2
    assert beats[0].transition_profile == "setup"
    assert beats[1].transition_profile == "conclusion"
    assert beats[0].emphasis == "context"
    assert beats[1].emphasis == "key"
    assert beats[0].wire_pulse is False
    assert beats[1].wire_pulse is False


def test_cmos_scene_uses_intro_safe_hud_copy() -> None:
    mod = _load_cmos_module()
    scene = mod.CMOSInverterScene()
    fixture = scene.build_fixture()
    title, intro = scene.hud_intro_texts(fixture)
    assert "P1" not in title
    assert "OUT" not in title
    assert "OUT" not in intro


def test_cmos_inverter_scene_construct_smoke() -> None:
    mod = _load_cmos_module()

    class _RecordingScene(mod.CMOSInverterScene):
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


def test_cmos_intro_annotations_hide_p1_n1_and_out() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, signals, bundle, _records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    waveform_panel, _panel_spec = WaveformPanelRenderer().render_with_layout(
        bundle, layout, idle_only=True
    )
    hide_labels(topology.components)
    hide_labels(waveform_panel)
    topology_labels = type(topology.components)(*detach_label_roots(topology.components))
    waveform_panel_labels = type(waveform_panel)(*detach_label_roots(waveform_panel))

    class _RecordingScene(mod.CMOSInverterScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

    scene = _RecordingScene()
    scene.play_intro_annotations(topology_labels, waveform_panel_labels)

    staged_component_labels = {
        label.text for label in iter_label_roots(topology_labels, roles=("component_label",))
    }
    staged_net_labels = {
        label.text for label in iter_label_roots(topology_labels, roles=("net_label",))
    }
    revealed_scene_labels = {
        label.text
        for label in iter_label_roots(
            VGroup(*scene.mobjects),
            roles=("component_label", "net_label"),
        )
    }
    assert staged_component_labels == {"P1", "N1"}
    assert staged_net_labels == {"OUT"}
    assert revealed_scene_labels == {"IN", "VCC", "GND"}


def test_cmos_construct_hides_detached_labels_before_intro_annotations() -> None:
    mod = _load_cmos_module()

    class _TracingScene(mod.CMOSInverterScene):
        def __init__(self) -> None:
            self.topology_intro_visible: set[str] | None = None
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            del animations, kwargs

        def wait(self, duration: float = 0.0) -> None:
            del duration

        def play_intro_annotations(self, topology_labels, waveform_panel_labels) -> None:
            del waveform_panel_labels
            self.topology_intro_visible = {
                label.text
                for label in iter_label_roots(topology_labels)
                if label_visible(label)
            }

    scene = _TracingScene()
    scene.construct()

    assert scene.topology_intro_visible == set()


def test_cmos_construct_reveals_scene_labels_in_phase_order() -> None:
    mod = _load_cmos_module()

    class _TracingScene(mod.CMOSInverterScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            self.snapshots: list[set[str]] = []
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))
            visible = scene_visible_label_texts(
                self,
                roles=("component_label", "net_label"),
            )
            self.snapshots.append(visible)

    scene = _TracingScene()
    scene.construct()

    play_roles = played_role_sets(scene.played)
    intro_component_index = next(
        i for i, roles in enumerate(play_roles) if roles == {"component_label"}
    )
    setup_component_index = next(
        i
        for i, roles in enumerate(
            play_roles[intro_component_index + 1 :],
            start=intro_component_index + 1,
        )
        if roles == {"component_label"}
    )
    conclusion_net_index = next(i for i, roles in enumerate(play_roles) if roles == {"net_label"})

    assert scene.snapshots[0] == set()
    assert scene.snapshots[4] == set()
    assert scene.snapshots[intro_component_index] == {"IN", "VCC", "GND"}
    assert scene.snapshots[setup_component_index - 1] == {"IN", "VCC", "GND"}
    assert scene.snapshots[setup_component_index] == {"IN", "VCC", "GND", "P1", "N1"}
    assert scene.snapshots[conclusion_net_index - 1] == {"IN", "VCC", "GND", "P1", "N1"}
    assert scene.snapshots[conclusion_net_index] == {"IN", "VCC", "GND", "P1", "N1", "OUT"}


def test_cmos_construct_reveals_hud_roles_in_phase_order() -> None:
    mod = _load_cmos_module()

    class _TracingScene(mod.CMOSInverterScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

    scene = _TracingScene()
    scene.construct()

    play_roles = played_role_sets(scene.played)
    hud_title_index = next(i for i, roles in enumerate(play_roles) if roles == {"hud.title"})
    hud_intro_index = next(i for i, roles in enumerate(play_roles) if roles == {"hud.intro"})
    first_caption_index = next(
        i
        for i, roles in enumerate(play_roles)
        if roles == {"hud.caption", "hud.intro", "hud.title"}
    )
    second_caption_index = next(
        i
        for i, roles in enumerate(
            play_roles[first_caption_index + 1 :],
            start=first_caption_index + 1,
        )
        if roles == {"hud.caption"}
    )

    assert hud_title_index < hud_intro_index < first_caption_index < second_caption_index


def test_default_label_phase_policy_hides_device_and_net_labels_in_intro() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, _signals, _bundle, _records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    policy = LabelPhasePolicy()

    intro_allowed = {
        label.text
        for label in iter_label_roots(topology.components)
        if label_allowed_in_phase(label, "intro_annotation", policy)
    }
    device_labels = {
        label.text
        for label in iter_label_roots(topology.components, roles=("component_label",))
        if label_category(label) == "device"
    }
    net_labels = {
        label.text
        for label in iter_label_roots(topology.components, roles=("net_label",))
    }

    assert intro_allowed == {"IN", "VCC", "GND"}
    assert device_labels == {"P1", "N1"}
    assert net_labels == {"OUT"}


def test_detached_label_roots_remove_topology_labels_from_intro_geometry() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, _signals, _bundle, _records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    detached = detach_label_roots(topology.components)
    detached_texts = {label.text for label in detached}
    remaining_texts = {label.text for label in iter_label_roots(topology.components)}

    assert {"P1", "N1", "OUT"}.issubset(detached_texts)
    assert remaining_texts == set()


def test_refresh_label_strokes_keeps_hidden_device_and_net_labels_hidden() -> None:
    mod = _load_cmos_module()
    graph, elements, layout, _signals, _bundle, _records = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    hide_labels(topology.components)
    refresh_label_strokes(topology.components, mode="full")

    hidden_labels = {
        label.text
        for label in iter_label_roots(topology.components)
        if not label_visible(label)
    }
    assert {"P1", "N1", "OUT"}.issubset(hidden_labels)


def test_cmos_intro_static_redraw_matches_live_frame() -> None:
    mod = _load_cmos_module()

    class _ProbeScene(mod.CMOSInverterScene):
        def __init__(self) -> None:
            self.redraw_diff_bbox = None
            super().__init__()

        def construct(self) -> None:
            fixture = self.build_fixture()
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
            from manim_engineering.animation.scene import configure_waveform_scene_camera

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


def test_cmos_prebeat_static_redraw_matches_live_frame() -> None:
    mod = _load_cmos_module()

    class _ProbeScene(mod.CMOSInverterScene):
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
            reveal_tracker = WaveformRevealTracker(
                waveform_panel,
                fixture.bundle,
                panel_spec,
                WaveformPanelRenderer(),
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
