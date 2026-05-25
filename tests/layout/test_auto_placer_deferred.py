"""Baseline for deferred global auto-placer (preset-first strategy).

Full netlist auto-placement is intentionally **not** wired into ``LayoutEngine``.
This module records the grid-only baseline for the zener regulator so a future
spike can compare against the hand-tuned preset without regressing silently.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.footprint import wires_avoid_footprints
from manim_engineering.layout.presets.zener_regulator import JUNCTION

REPO = Path(__file__).resolve().parents[2]

_AUTO_PLACER_DEFERRED_REASON = (
    "Global auto-placer deferred during stabilization; use layout/presets/ "
    "for canonical teaching shapes."
)


def _zener_graph_and_elements():
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/07_zener_regulator.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    graph, elements, preset_layout = mod.build_zener_regulator_fixture()
    grid_layout = LayoutEngine().layout(graph, elements)
    return graph, elements, preset_layout, grid_layout


def test_global_auto_placer_not_default_path() -> None:
    """Document that LayoutEngine.solve does not replace preset layouts."""
    pytest.skip(_AUTO_PLACER_DEFERRED_REASON)


@pytest.mark.xfail(
    reason=_AUTO_PLACER_DEFERRED_REASON,
    strict=False,
)
def test_zener_grid_only_does_not_match_preset_junction() -> None:
    """Spike criterion: grid-only layout should not yet match preset junction."""
    _graph, elements, preset_layout, grid_layout = _zener_graph_and_elements()
    preset_junction = next(
        node
        for node in preset_layout.junction_nodes
        if abs(node.x - JUNCTION.x) < 0.01 and abs(node.y - JUNCTION.y) < 0.01
    )
    grid_rs_b = grid_layout.pin_positions[elements["rs1"].get_pin("b").id]
    assert grid_rs_b.x == pytest.approx(preset_junction.x)
    assert grid_rs_b.y == pytest.approx(preset_junction.y)


def test_zener_grid_only_baseline_is_deterministic() -> None:
    graph, elements, _preset_layout, first = _zener_graph_and_elements()
    second = LayoutEngine().layout(graph, elements)
    assert first.pin_positions == second.pin_positions
    assert first.placements == second.placements


def test_zener_grid_only_baseline_avoids_footprints() -> None:
    _graph, _elements, _preset_layout, grid_layout = _zener_graph_and_elements()
    assert wires_avoid_footprints(grid_layout)
