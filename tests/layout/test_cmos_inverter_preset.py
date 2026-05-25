"""CMOS inverter preset layout tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout.footprint import assert_wires_avoid_footprints
from manim_engineering.layout.presets.cmos_inverter import (
    DRAIN_Y,
    GATE_BUS_X,
    GATE_BUS_Y,
    GND_Y,
    NMOS_DRAIN_Y,
    OUT_X,
    PMOS_DRAIN_Y,
    RAIL_X,
    VCC_Y,
)

REPO = Path(__file__).resolve().parents[2]


def _load_fixture():
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/03_cmos_inverter.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_inverter_fixture()


def test_cmos_vertical_stack_three_node_topology() -> None:
    _graph, elements, layout = _load_fixture()
    assert OUT_X != pytest.approx(RAIL_X)

    pmos_drain = layout.pin_positions[elements["pm1"].get_pin("drain").id]
    nmos_drain = layout.pin_positions[elements["nm1"].get_pin("drain").id]
    assert pmos_drain.x == pytest.approx(OUT_X)
    assert nmos_drain.x == pytest.approx(OUT_X)
    assert pmos_drain.y == pytest.approx(PMOS_DRAIN_Y)
    assert nmos_drain.y == pytest.approx(NMOS_DRAIN_Y)
    assert pmos_drain.y == pytest.approx(nmos_drain.y)

    pmos_source = layout.pin_positions[elements["pm1"].get_pin("source").id]
    nmos_source = layout.pin_positions[elements["nm1"].get_pin("source").id]
    assert pmos_source.y > nmos_source.y
    assert pmos_source.x == pytest.approx(RAIL_X)
    assert nmos_source.x == pytest.approx(RAIL_X)

    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]
    gnd_pin = layout.pin_positions[elements["gnd1"].get_pin("gnd").id]
    assert vcc_pin.x == pytest.approx(RAIL_X)
    assert gnd_pin.x == pytest.approx(RAIL_X)
    assert vcc_pin.y == pytest.approx(pmos_source.y)
    assert gnd_pin.y == pytest.approx(nmos_source.y)
    assert vcc_pin.y > pmos_drain.y
    assert gnd_pin.y < nmos_drain.y

    in_out = layout.pin_positions[elements["in_drv"].get_pin("out").id]
    pmos_gate = layout.pin_positions[elements["pm1"].get_pin("gate").id]
    nmos_gate = layout.pin_positions[elements["nm1"].get_pin("gate").id]
    assert in_out.y == pytest.approx(GATE_BUS_Y)
    assert in_out.x < GATE_BUS_X
    assert pmos_gate.x == pytest.approx(nmos_gate.x)
    assert pmos_gate.y > nmos_gate.y

    assert_wires_avoid_footprints(layout)


def test_cmos_vertical_spine_sdds_order() -> None:
    """Main terminals read S–D–D–S from top to bottom."""
    _graph, elements, layout = _load_fixture()
    pmos_source = layout.pin_positions[elements["pm1"].get_pin("source").id]
    pmos_drain = layout.pin_positions[elements["pm1"].get_pin("drain").id]
    nmos_drain = layout.pin_positions[elements["nm1"].get_pin("drain").id]
    nmos_source = layout.pin_positions[elements["nm1"].get_pin("source").id]
    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]
    gnd_pin = layout.pin_positions[elements["gnd1"].get_pin("gnd").id]

    assert vcc_pin.y == pytest.approx(VCC_Y)
    assert gnd_pin.y == pytest.approx(GND_Y)
    assert pmos_source.y == pytest.approx(VCC_Y)
    assert nmos_source.y == pytest.approx(GND_Y)
    assert pmos_source.y > pmos_drain.y
    assert nmos_drain.y > nmos_source.y
    assert pmos_drain.y == pytest.approx(nmos_drain.y)
