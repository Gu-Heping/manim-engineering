"""Pin-aligned placement helper tests."""

from __future__ import annotations

import pytest

from manim_engineering.components import Resistor
from manim_engineering.layout import origin_for_pin_at, pin_world_position
from manim_engineering.layout.presets.opamp import GND_CHANNEL_Y
from manim_engineering.layout.types import ComponentPlacement, Point2D


def test_origin_for_pin_at_places_pin_at_target() -> None:
    r = Resistor("r1", label="R1")
    target = Point2D(2.0, 3.0)
    origin = origin_for_pin_at(r, "a", target)
    placement = ComponentPlacement("r1", origin, r.get_bounds())
    assert pin_world_position(placement, r, "a") == target


def test_opamp_gnd_route_avoids_in_n() -> None:
    mod_path = __import__("pathlib").Path(__file__).resolve().parents[2] / (
        "examples/analog/05_opamp_inverting.py"
    )
    import importlib.util

    spec = importlib.util.spec_from_file_location("opamp_inv", mod_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _graph, elements, layout = mod.build_opamp_inverting_fixture()
    op = elements["op1"]
    in_n = layout.pin_positions[op.get_pin("in_n").id]
    layout.pin_positions[op.get_pin("in_p").id]
    gnd_pin = layout.pin_positions[elements["gnd1"].get_pin("gnd").id]

    gnd_wire = next(
        w for w in layout.wires if "in_p" in w.connection_id and "gnd" in w.connection_id
    )
    for seg in gnd_wire.segments:
        if abs(seg.start.x - in_n.x) < 0.01 and abs(seg.end.x - in_n.x) < 0.01:
            lo = min(seg.start.y, seg.end.y)
            hi = max(seg.start.y, seg.end.y)
            assert not (lo < in_n.y < hi), "GND wire must not pass through in_n"
    assert gnd_pin.y == pytest.approx(GND_CHANNEL_Y)
    assert any(
        pt.y == GND_CHANNEL_Y for pt in gnd_wire.points
    ), "GND route should use the low channel below the summation bus"
