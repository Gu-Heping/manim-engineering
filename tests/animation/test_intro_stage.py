"""IntroStage: stroke-first topology reveal without white Line fill artifacts."""

from __future__ import annotations

import importlib.util
from unittest.mock import patch

import pytest

pytest.importorskip("manim")

from manim import Scene, VGroup, tempconfig

from manim_engineering.animation import play_topology_intro
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer

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


def _symbol_lines(root) -> list:
    return [
        mob
        for mob in root.get_family()
        if mob.__class__.__name__ == "Line" and len(mob.points) > 0
    ]


def test_play_topology_intro_keeps_symbol_lines_stroke_only() -> None:
    topology, panel, content = _rc_fixture()

    class _IntroScene(Scene):
        def construct(self) -> None:
            play_topology_intro(
                self,
                topology,
                panel,
                content,
                components_run_time=0.4,
                wires_run_time=0.3,
                panel_run_time=0.3,
                lag_ratio=0.25,
                total_run_time=0.8,
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
                    components_run_time=0.2,
                    wires_run_time=0.2,
                    panel_run_time=0.2,
                    lag_ratio=0.25,
                    total_run_time=0.4,
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
                        components_run_time=0.2,
                        wires_run_time=0.2,
                        panel_run_time=0.2,
                        lag_ratio=0.25,
                        total_run_time=0.4,
                    )
            comp_opacity.assert_not_called()
            wire_opacity.assert_not_called()

    with tempconfig({"quality": "low_quality", "disable_caching": True, "write_to_movie": False}):
        _IntroScene().render()
