"""Intro plan builder keeps stable stage order for teaching-scene intros."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import VGroup

from manim_engineering.animation import IntroPlan, build_intro_plan
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer

REPO = Path(__file__).resolve().parents[2]


def _load_module(rel_path: str):
    path = REPO / rel_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rc_fixture():
    mod = _load_module("examples/analog/01_rc_charge.py")
    graph, elements, layout, _, bundle, _ = mod.build_rc_teaching_fixture()
    topology = ManimRenderer().render_topology(graph, layout, dict(elements))
    panel, _ = WaveformPanelRenderer().render_with_layout(bundle, layout, idle_only=True)
    return topology, panel


def test_build_intro_plan_returns_default_stage_order() -> None:
    topology, panel = _rc_fixture()
    plan = build_intro_plan(topology, panel)
    assert isinstance(plan, IntroPlan)
    assert tuple(stage.name for stage in plan.stages) == ("components", "wires", "panel")
    assert all(stage.strokes for stage in plan.stages)


def test_build_intro_plan_tracks_panel_trace_policy() -> None:
    topology, panel = _rc_fixture()
    chrome_only = build_intro_plan(topology, panel, include_panel_traces=False)
    with_traces = build_intro_plan(topology, panel, include_panel_traces=True)
    chrome_count = next(stage for stage in chrome_only.stages if stage.name == "panel")
    trace_count = next(stage for stage in with_traces.stages if stage.name == "panel")
    assert chrome_only.include_panel_traces is False
    assert with_traces.include_panel_traces is True
    assert len(trace_count.strokes) >= len(chrome_count.strokes)


def test_build_intro_plan_omits_empty_panel_stage() -> None:
    topology, _panel = _rc_fixture()
    plan = build_intro_plan(topology, VGroup())
    assert tuple(stage.name for stage in plan.stages) == ("components", "wires")
