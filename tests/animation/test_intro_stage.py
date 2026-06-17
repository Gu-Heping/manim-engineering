"""IntroStage: stroke-first topology reveal without white Line fill artifacts."""

from __future__ import annotations

import importlib.util
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("manim")

from manim import Scene, VGroup, tempconfig

from manim_engineering.animation import play_topology_intro
from manim_engineering.animation.intro_style import IntroStyle, intro_run_time_budget
from manim_engineering.animation.scene_template import (
    _intro_anims_for_strokes,
    _iter_trace_line_strokes,
)
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.renderers.minimal.labels import (
    iter_label_roots,
    iter_symbol_strokes,
    label_role,
    prepare_stroke_reveal,
    restore_stroke_reveal,
)

REPO = pytest.importorskip("pathlib").Path(__file__).resolve().parents[2]


def _rc_fixture():
    spec = importlib.util.spec_from_file_location(
        "rc_charge",
        REPO / "examples/analog/01_rc_charge.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    graph, elements, layout, _, bundle, _ = mod.build_rc_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    panel, panel_spec = WaveformPanelRenderer().render_with_layout(
        bundle, layout, idle_only=True
    )
    content = VGroup(topology.components, topology.wires, panel)
    return topology, panel, content


def _cmos_fixture():
    spec = importlib.util.spec_from_file_location(
        "cmos_inverter",
        REPO / "examples/analog/03_cmos_inverter.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    graph, elements, layout, _, bundle, _ = mod.build_cmos_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    panel, _panel_spec = WaveformPanelRenderer().render_with_layout(
        bundle, layout, idle_only=True
    )
    content = VGroup(topology.components, topology.wires, panel)
    return topology, panel, content


def _symbol_lines(root) -> list:
    return [
        mob
        for mob in root.get_family()
        if mob.__class__.__name__ == "Line" and len(mob.points) > 0
    ]


def _label_visible(label) -> bool:
    for sub in label.get_family():
        if len(sub.points) == 0:
            continue
        if float(sub.get_fill_opacity()) > 0.01:
            return True
    return False


def test_intro_run_time_budget_scales_with_stroke_count() -> None:
    style = IntroStyle(per_stroke_run_time=0.10, min_stage_run_time=0.5)
    assert intro_run_time_budget(0, style) == pytest.approx(0.5)
    assert intro_run_time_budget(5, style) == pytest.approx(0.65)
    assert intro_run_time_budget(50, style) == pytest.approx(4.0)


def test_play_topology_intro_uses_staged_plays() -> None:
    topology, panel, content = _rc_fixture()
    component_count = len(iter_symbol_strokes(topology.components))
    wire_count = len(iter_symbol_strokes(topology.wires))
    style = IntroStyle(per_stroke_run_time=0.10, min_stage_run_time=0.5)
    min_expected = intro_run_time_budget(component_count, style) + intro_run_time_budget(
        wire_count, style
    )

    scene = MagicMock()
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        include_panel_traces=False,
        intro_style=style,
    )

    assert scene.play.call_count >= 2
    total_run_time = sum(call.kwargs.get("run_time", 0.0) for call in scene.play.call_args_list)
    assert total_run_time >= min_expected * 0.95


def test_play_topology_intro_can_play_components_in_layout_order() -> None:
    topology, panel, content = _rc_fixture()
    scene = MagicMock()
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        component_order="layout",
        components_run_time=1.2,
        wires_run_time=0.3,
        panel_run_time=0.2,
        include_panel_traces=False,
        intro_style=IntroStyle(),
    )

    assert scene.play.call_count >= topology.n_components + 2
    component_stage_run_times = [
        call.kwargs.get("run_time")
        for call in scene.play.call_args_list[: topology.n_components]
    ]
    assert component_stage_run_times
    assert all(
        run_time == pytest.approx(1.2 / topology.n_components)
        for run_time in component_stage_run_times
    )


def test_play_topology_intro_restores_strokes_after_each_stage() -> None:
    topology, panel, content = _rc_fixture()
    component_strokes = iter_symbol_strokes(topology.components)
    wire_strokes = iter_symbol_strokes(topology.wires)

    scene = MagicMock()
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        include_panel_traces=False,
        intro_style=IntroStyle(),
    )

    for stroke in (*component_strokes, *wire_strokes):
        assert float(stroke.get_stroke_opacity()) == pytest.approx(1.0)


def test_intro_stage_uses_flat_lagged_start() -> None:
    topology, panel, content = _rc_fixture()
    component_strokes = iter_symbol_strokes(topology.components)
    anim = _intro_anims_for_strokes(component_strokes, intro_style=IntroStyle())
    assert anim.__class__.__name__ == "LaggedStart"
    for sub in anim.animations:
        assert sub.__class__.__name__ in ("Create", "DrawBorderThenFill")


def test_restore_stroke_reveal_after_prepare() -> None:
    topology, panel, content = _rc_fixture()
    strokes = iter_symbol_strokes(topology.components)
    prepare_stroke_reveal(strokes)
    restore_stroke_reveal(strokes)
    for stroke in strokes:
        assert float(stroke.get_stroke_opacity()) == pytest.approx(1.0)


def test_play_topology_intro_excludes_trace_lines_by_default() -> None:
    topology, panel, content = _rc_fixture()
    trace_lines = _iter_trace_line_strokes(panel)
    assert trace_lines

    played_anims: list[object] = []

    scene = MagicMock()

    def _capture_play(anim, *, run_time=0.0):
        played_anims.append(anim)

    scene.play = _capture_play
    scene.add = MagicMock()

    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        include_panel_traces=False,
        intro_style=IntroStyle(),
    )

    played_mobs = set()
    for anim in played_anims:
        for mob in getattr(anim, "mobjects", []) or []:
            played_mobs.add(id(mob))
        if hasattr(anim, "animations"):
            for sub in anim.animations:
                for mob in getattr(sub, "mobjects", []) or []:
                    played_mobs.add(id(mob))

    for line in trace_lines:
        assert id(line) not in played_mobs
        assert float(line.get_stroke_opacity()) == pytest.approx(0.0)


def test_play_topology_intro_can_keep_net_labels_hidden() -> None:
    topology, panel, content = _cmos_fixture()
    net_labels = [
        label for label in iter_label_roots(topology.components) if label_role(label) == "net_label"
    ]
    component_labels = [
        label
        for label in iter_label_roots(topology.components)
        if label_role(label) == "component_label"
    ]
    assert net_labels
    assert component_labels

    scene = MagicMock()
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        include_panel_traces=False,
        intro_style=IntroStyle(),
        reveal_component_labels=True,
        reveal_net_labels=False,
        reveal_panel_labels=False,
    )

    assert all(_label_visible(label) for label in component_labels)
    assert all(not _label_visible(label) for label in net_labels)


def test_play_topology_intro_keeps_symbol_lines_stroke_only() -> None:
    topology, panel, content = _rc_fixture()

    class _IntroScene(Scene):
        def construct(self) -> None:
            play_topology_intro(
                self,
                topology,
                panel,
                content,
                include_panel_traces=True,
                total_run_time=2.0,
            )
            lines = _symbol_lines(topology.components)
            assert lines
            for line in lines:
                assert float(line.get_fill_opacity()) == pytest.approx(0.0)
                assert line.get_stroke_width() > 0
                assert float(line.get_stroke_opacity()) == pytest.approx(1.0)
            panel_lines = _symbol_lines(panel)
            assert panel_lines
            for line in panel_lines:
                assert float(line.get_fill_opacity()) == pytest.approx(0.0)
                assert line.get_stroke_width() > 0
                assert float(line.get_stroke_opacity()) == pytest.approx(1.0)

    with tempconfig({"quality": "low_quality", "disable_caching": True, "write_to_movie": False}):
        _IntroScene().render()


def test_play_topology_intro_does_not_call_panel_set_opacity() -> None:
    topology, panel, content = _rc_fixture()

    class _IntroScene(Scene):
        def construct(self) -> None:
            with patch.object(panel, "set_opacity") as panel_opacity:
                play_topology_intro(
                    self,
                    topology,
                    panel,
                    content,
                    total_run_time=1.5,
                )
            panel_opacity.assert_not_called()

    with tempconfig({"quality": "low_quality", "disable_caching": True, "write_to_movie": False}):
        _IntroScene().render()


def test_play_topology_intro_does_not_call_components_set_opacity() -> None:
    topology, panel, content = _rc_fixture()

    class _IntroScene(Scene):
        def construct(self) -> None:
            with patch.object(topology.components, "set_opacity") as comp_opacity:
                with patch.object(topology.wires, "set_opacity") as wire_opacity:
                    play_topology_intro(
                        self,
                        topology,
                        panel,
                        content,
                        total_run_time=1.5,
                    )
            comp_opacity.assert_not_called()
            wire_opacity.assert_not_called()

    with tempconfig({"quality": "low_quality", "disable_caching": True, "write_to_movie": False}):
        _IntroScene().render()
