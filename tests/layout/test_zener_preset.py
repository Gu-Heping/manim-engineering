"""Zener regulator preset layout tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout.footprint import assert_wires_avoid_footprints
from manim_engineering.layout.presets.zener_regulator import JUNCTION, RL_BRANCH_X, VCC_Y

REPO = Path(__file__).resolve().parents[2]


def _load_fixture():
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/07_zener_regulator.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_zener_regulator_fixture()


def test_zener_junction_branch_topology() -> None:
    _graph, elements, layout = _load_fixture()
    rs_b = layout.pin_positions[elements["rs1"].get_pin("b").id]
    rl_a = layout.pin_positions[elements["rl1"].get_pin("a").id]
    zd_cathode = layout.pin_positions[elements["zd1"].get_pin("cathode").id]
    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]

    assert rs_b.x == pytest.approx(JUNCTION.x)
    assert rs_b.y == pytest.approx(JUNCTION.y)
    assert rl_a.x == pytest.approx(RL_BRANCH_X)
    assert rl_a.y == pytest.approx(JUNCTION.y)
    assert zd_cathode.x == pytest.approx(JUNCTION.x)
    assert zd_cathode.y < JUNCTION.y
    assert vcc_pin.x == pytest.approx(JUNCTION.x)
    assert vcc_pin.y == pytest.approx(VCC_Y)

    rs_a = layout.pin_positions[elements["rs1"].get_pin("a").id]
    assert vcc_pin.x == pytest.approx(rs_a.x)
    assert vcc_pin.y == pytest.approx(rs_a.y)
    assert vcc_pin in layout.junction_nodes

    assert_wires_avoid_footprints(layout)
