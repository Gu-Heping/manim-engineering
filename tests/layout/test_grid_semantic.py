"""Grid semantic layering tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.components import VCC, Capacitor, Ground, InputDriver, Resistor
from manim_engineering.core import SignalType
from manim_engineering.layout import place_on_grid_semantic

REPO = Path(__file__).resolve().parents[2]


def test_place_on_grid_semantic_layers_gnd_below_signal_chain() -> None:
    drv = InputDriver("drv", signal_type=SignalType.DIGITAL)
    r1 = Resistor("r1")
    c1 = Capacitor("c1")
    gnd = Ground("gnd")
    placements = place_on_grid_semantic((drv, r1, c1, gnd))
    by_id = {placement.element_id: placement for placement in placements}

    assert by_id["drv"].origin.y > by_id["gnd"].origin.y
    assert by_id["r1"].origin.x > by_id["drv"].origin.x
    assert by_id["c1"].origin.x > by_id["r1"].origin.x
    assert by_id["gnd"].origin.x > by_id["c1"].origin.x


def test_place_on_grid_semantic_layers_vcc_above_signal_chain() -> None:
    vcc = VCC("vcc")
    r1 = Resistor("r1")
    gnd = Ground("gnd")
    placements = place_on_grid_semantic((vcc, r1, gnd))
    by_id = {placement.element_id: placement for placement in placements}

    assert by_id["vcc"].origin.y > by_id["r1"].origin.y
    assert by_id["r1"].origin.y > by_id["gnd"].origin.y
    assert by_id["vcc"].origin.x == pytest.approx(by_id["r1"].origin.x)


def test_rc_charge_fixture_uses_semantic_layers() -> None:
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/01_rc_charge.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _graph, elements, layout = mod.build_rc_charge_fixture()

    placements = {p.element_id: p for p in layout.placements}
    assert placements["drv"].origin.y > placements["gnd"].origin.y
    assert placements["r1"].origin.y == pytest.approx(placements["drv"].origin.y)
