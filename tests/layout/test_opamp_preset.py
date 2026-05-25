"""Op-amp preset layout and routing regression tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout.footprint import assert_wires_avoid_footprints
from manim_engineering.layout.presets.opamp import FEEDBACK_Y, GND_CHANNEL_Y, INPUT_COL_X, OP_X, SUMMATION_Y
from manim_engineering.layout.routing import points_to_segments, segments_intersect

REPO = Path(__file__).resolve().parents[2]


def _load_fixture(rel_path: str, builder: str):
    spec = importlib.util.spec_from_file_location("fixture", REPO / rel_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, builder)()


def _segment_crosses_opamp_input_column(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    in_p_y: float,
    in_n_y: float,
    input_col_x: float,
) -> bool:
    """True when a vertical segment at the +/- stub column spans both input pins."""
    if x0 != x1:
        return False
    if abs(x0 - input_col_x) > 0.05:
        return False
    lo, hi = sorted((y0, y1))
    return lo < in_n_y < hi and lo < in_p_y < hi


def test_opamp_inverting_summation_bus_left_of_opamp() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/05_opamp_inverting.py",
        "build_opamp_inverting_fixture",
    )
    op = elements["op1"]
    in_p_y = layout.pin_positions[op.get_pin("in_p").id].y
    in_n_y = layout.pin_positions[op.get_pin("in_n").id].y
    input_col_x = layout.pin_positions[op.get_pin("in_n").id].x
    rin_b = layout.pin_positions[elements["rin1"].get_pin("b").id]
    assert rin_b.x == pytest.approx(INPUT_COL_X)
    assert rin_b.x < OP_X

    for wire in layout.wires:
        for seg in wire.segments:
            assert not _segment_crosses_opamp_input_column(
                seg.start.x,
                seg.start.y,
                seg.end.x,
                seg.end.y,
                in_p_y=in_p_y,
                in_n_y=in_n_y,
                input_col_x=input_col_x,
            )

    assert_wires_avoid_footprints(layout)


def test_opamp_flip_y_places_in_n_above_in_p_and_aligns_summation() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/05_opamp_inverting.py",
        "build_opamp_inverting_fixture",
    )
    op = elements["op1"]
    in_p_y = layout.pin_positions[op.get_pin("in_p").id].y
    in_n_y = layout.pin_positions[op.get_pin("in_n").id].y
    rin_b = layout.pin_positions[elements["rin1"].get_pin("b").id]
    placement = next(p for p in layout.placements if p.element_id == op.element_id)

    assert in_n_y > in_p_y
    assert rin_b.y == pytest.approx(in_n_y)
    assert rin_b.y == pytest.approx(SUMMATION_Y)
    assert placement.orientation.flip_y

    in_n = layout.pin_positions[op.get_pin("in_n").id]
    out = layout.pin_positions[op.get_pin("out").id]
    assert in_n.x == pytest.approx(OP_X)
    assert in_n.x != pytest.approx(INPUT_COL_X)
    assert out.x == pytest.approx(OP_X + op.get_bounds().width)


def test_opamp_integrator_feedback_drops_at_output_column() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/06_opamp_integrator.py",
        "build_opamp_integrator_fixture",
    )
    out = layout.pin_positions[elements["op1"].get_pin("out").id]
    drop_segments = [
        seg
        for wire in layout.wires
        for seg in wire.segments
        if abs(seg.start.x - out.x) < 0.01
        and abs(seg.end.x - out.x) < 0.01
        and seg.start.y != seg.end.y
    ]
    assert drop_segments
    assert any(
        max(seg.start.y, seg.end.y) >= FEEDBACK_Y - 0.01
        and min(seg.start.y, seg.end.y) <= out.y + 0.01
        for seg in drop_segments
    )
    assert_wires_avoid_footprints(layout)


def test_opamp_gnd_route_avoids_summation_bus() -> None:
    _graph, _elements, layout = _load_fixture(
        "examples/analog/05_opamp_inverting.py",
        "build_opamp_inverting_fixture",
    )
    gnd_conn = next(
        w for w in layout.wires if "in_p" in w.connection_id and "gnd" in w.connection_id
    )
    summation_bus = next(
        seg
        for wire in layout.wires
        if wire.connection_id.startswith("net-")
        for seg in wire.segments
        if seg.start.x == seg.end.x == INPUT_COL_X and seg.start.y != seg.end.y
    )
    for seg in gnd_conn.segments:
        assert not segments_intersect(seg, summation_bus)
    assert any(pt.y == GND_CHANNEL_Y for pt in gnd_conn.points)


def test_opamp_wires_have_no_zero_length_segments() -> None:
    _graph, _elements, layout = _load_fixture(
        "examples/analog/06_opamp_integrator.py",
        "build_opamp_integrator_fixture",
    )
    for wire in layout.wires:
        for seg in wire.segments:
            assert seg.start.x != seg.end.x or seg.start.y != seg.end.y
    assert layout.junction_nodes
