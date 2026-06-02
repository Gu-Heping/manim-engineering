"""Geometry-aware topology intro: Line Create vs Polygon DrawBorderThenFill."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, LaggedStart, VGroup
from scene_trace import trace_stage_entries

from manim_engineering.animation import IntroStyle, play_topology_intro
from manim_engineering.animation.trace import flush_trace, reset_tracer
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.renderers.minimal.labels import iter_symbol_strokes, partition_symbol_strokes

REPO = Path(__file__).resolve().parents[2]


def _load_module(rel_path: str):
    path = REPO / rel_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cmos_fixture():
    mod = _load_module("examples/analog/03_cmos_inverter.py")
    graph, elements, layout = mod.build_inverter_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    panel = VGroup()
    content = VGroup(topology.components, topology.wires, panel)
    return topology, panel, content


def _animation_type_names(animation: object) -> set[str]:
    names: set[str] = {animation.__class__.__name__}
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        for child in animation.animations:
            names |= _animation_type_names(child)
    return names


def test_partition_symbol_strokes_separates_line_and_filled() -> None:
    topology, _, _ = _cmos_fixture()
    strokes = iter_symbol_strokes(topology.components)
    line_strokes, filled_strokes = partition_symbol_strokes(strokes)
    assert line_strokes
    assert filled_strokes
    assert all(mob.__class__.__name__ == "Line" for mob in line_strokes)
    assert all(mob.__class__.__name__ in ("Polygon", "Dot") for mob in filled_strokes)
    assert len(line_strokes) + len(filled_strokes) == len(strokes)


def test_play_topology_intro_uses_draw_border_then_fill_by_default() -> None:
    topology, panel, content = _cmos_fixture()
    scene = MagicMock()
    captured: list[object] = []

    def _capture_play(*animations, **kwargs) -> None:
        del kwargs
        captured.extend(animations)

    scene.play = _capture_play
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        components_run_time=0.4,
        wires_run_time=0.3,
        panel_run_time=0.2,
        lag_ratio=0.25,
        total_run_time=0.8,
    )
    assert captured
    names = _animation_type_names(captured[0])
    assert "Create" in names
    assert "DrawBorderThenFill" in names


def test_play_topology_intro_border_fill_disabled_uses_create_only() -> None:
    topology, panel, content = _cmos_fixture()
    scene = MagicMock()
    captured: list[object] = []

    def _capture_play(*animations, **kwargs) -> None:
        del kwargs
        captured.extend(animations)

    scene.play = _capture_play
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        components_run_time=0.4,
        wires_run_time=0.3,
        panel_run_time=0.2,
        lag_ratio=0.25,
        total_run_time=0.8,
        intro_style=IntroStyle(use_border_fill=False),
    )
    assert captured
    names = _animation_type_names(captured[0])
    assert "Create" in names
    assert "DrawBorderThenFill" not in names


def test_play_topology_intro_records_geometry_trace_detail(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("DEBUG_SNAPSHOT_DIR", str(tmp_path))
    reset_tracer()
    topology, panel, content = _cmos_fixture()
    scene = MagicMock()
    scene.play = MagicMock()
    play_topology_intro(
        scene,
        topology,
        panel,
        content,
        components_run_time=0.2,
        wires_run_time=0.2,
        panel_run_time=0.2,
        lag_ratio=0.25,
        total_run_time=0.4,
    )
    path = flush_trace(scene)
    assert path is not None
    detail = trace_stage_entries(path, "intro.topology")[0]["detail"]
    assert detail["line_stroke_count"] > 0
    assert detail["filled_stroke_count"] > 0
    assert detail["use_border_fill"] is True


def test_intro_style_exported_from_animation_package() -> None:
    from manim_engineering.animation import IntroStyle as exported

    assert exported(border_fill_run_time=0.5).use_border_fill is True
