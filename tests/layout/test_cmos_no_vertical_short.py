"""CMOS inverter must not draw a rail-column dead short (VCC to GND)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import Line, VGroup

from manim_engineering.layout.presets.cmos_inverter import (
    GND_Y,
    NMOS_DRAIN_Y,
    PMOS_DRAIN_Y,
    RAIL_X,
    VCC_Y,
)
from manim_engineering.renderers.minimal import MinimalRenderer

REPO = Path(__file__).resolve().parents[2]

X_TOL = 0.03
Y_TOL = 0.05


def _load_fixture():
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/03_cmos_inverter.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_inverter_fixture()


def _iter_lines(group: VGroup):
    for sub in group.submobjects:
        if isinstance(sub, Line):
            yield sub
        elif isinstance(sub, VGroup):
            yield from _iter_lines(sub)


def _is_vertical_at_rail(line: Line) -> bool:
    x0 = float(line.get_start()[0])
    x1 = float(line.get_end()[0])
    if abs(x0 - x1) > X_TOL:
        return False
    if abs(x0 - RAIL_X) > X_TOL:
        return False
    y0 = float(line.get_start()[1])
    y1 = float(line.get_end()[1])
    y_min = min(y0, y1)
    y_max = max(y0, y1)
    return y_min <= GND_Y + Y_TOL and y_max >= VCC_Y - Y_TOL


def test_cmos_render_has_no_rail_column_dead_short() -> None:
    graph, elements, layout = _load_fixture()
    mob = MinimalRenderer().render_circuit(graph, layout, elements)
    offenders = [line for line in _iter_lines(mob) if _is_vertical_at_rail(line)]
    assert not offenders, (
        f"found {len(offenders)} vertical line(s) at x≈{RAIL_X} spanning GND→VCC; "
        f"drain node should be at OUT_X ({layout.pin_positions})"
    )


def test_cmos_drains_not_on_rail_column() -> None:
    _graph, elements, layout = _load_fixture()
    for key in ("pm1", "nm1"):
        drain = layout.pin_positions[elements[key].get_pin("drain").id]
        assert drain.x != pytest.approx(RAIL_X)
        assert drain.y == pytest.approx(PMOS_DRAIN_Y if key == "pm1" else NMOS_DRAIN_Y)
