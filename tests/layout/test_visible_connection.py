"""Visible stub routing for coincident pin connections."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout import (
    MIN_VISIBLE_STUB,
    ensure_visible_connection,
    points_to_segments,
    stub_direction_for_connection,
)
from manim_engineering.layout.footprint import assert_wires_avoid_footprints

REPO = Path(__file__).resolve().parents[2]


def _load_fixture(rel_path: str, builder: str):
    spec = importlib.util.spec_from_file_location("fixture", REPO / rel_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, builder)()


def test_ensure_visible_connection_expands_coincident_pins() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/04_npn_amplifier.py",
        "build_npn_amplifier_fixture",
    )
    connection = next(
        c for c in _graph.connections if "vcc" in c.id and "rc1.a" in c.id
    )
    from manim_engineering.layout.routing import merge_routing_hints

    shared = layout.pin_positions[connection.port_a.id]
    hints = merge_routing_hints(
        connection.port_a.routing_hints,
        connection.port_b.routing_hints,
    )
    points = ensure_visible_connection(
        (shared,),
        connection=connection,
        pin_positions=layout.pin_positions,
        placements_by_id={p.element_id: p for p in layout.placements},
        hints=hints,
    )
    segments = points_to_segments(points)
    assert len(segments) == 1
    length = abs(segments[0].end.x - segments[0].start.x) + abs(
        segments[0].end.y - segments[0].start.y
    )
    assert length >= MIN_VISIBLE_STUB - 1e-6


def test_stub_direction_avoids_resistor_interior() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/04_npn_amplifier.py",
        "build_npn_amplifier_fixture",
    )
    connection = next(
        c for c in _graph.connections if "vcc" in c.id and "rc1.a" in c.id
    )
    from manim_engineering.layout.routing import merge_routing_hints

    hints = merge_routing_hints(
        connection.port_a.routing_hints,
        connection.port_b.routing_hints,
    )
    origin = layout.pin_positions[connection.port_a.id]
    direction = stub_direction_for_connection(
        connection,
        layout.pin_positions,
        {p.element_id: p for p in layout.placements},
        hints=hints,
    )
    points = ensure_visible_connection(
        (origin,),
        connection=connection,
        pin_positions=layout.pin_positions,
        placements_by_id={p.element_id: p for p in layout.placements},
        hints=hints,
    )
    from manim_engineering.layout.footprint import segment_crosses_footprint_interior

    for segment in points_to_segments(points):
        for placement in layout.placements:
            assert not segment_crosses_footprint_interior(segment, placement)
    assert direction in ("+x", "-x", "+y", "-y")


def test_npn_vcc_rc_connection_is_visible() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/04_npn_amplifier.py",
        "build_npn_amplifier_fixture",
    )
    wire = next(w for w in layout.wires if "vcc" in w.connection_id and "rc1.a" in w.connection_id)
    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]
    rc_a = layout.pin_positions[elements["rc1"].get_pin("a").id]
    assert len(wire.segments) == 1
    seg = wire.segments[0]
    assert seg.start.y == seg.end.y == pytest.approx(vcc_pin.y)
    assert abs(seg.end.x - seg.start.x) >= MIN_VISIBLE_STUB - 1e-6
    assert seg.end.x == pytest.approx(rc_a.x)


def test_zener_vcc_rs_connection_is_visible() -> None:
    _graph, elements, layout = _load_fixture(
        "examples/analog/07_zener_regulator.py",
        "build_zener_regulator_fixture",
    )
    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]
    rs_a = layout.pin_positions[elements["rs1"].get_pin("a").id]
    assert vcc_pin.x == pytest.approx(rs_a.x)
    assert vcc_pin.y == pytest.approx(rs_a.y)
    assert vcc_pin in layout.junction_nodes
    assert_wires_avoid_footprints(layout)


def test_renderer_places_dot_at_electrical_junction() -> None:
    from manim import Dot

    from manim_engineering.renderers.minimal import MinimalRenderer

    graph, elements, layout = _load_fixture(
        "examples/analog/07_zener_regulator.py",
        "build_zener_regulator_fixture",
    )
    assert layout.junction_nodes
    mob = MinimalRenderer().render_layout(layout, graph, elements)
    dots = [sub for sub in mob.submobjects if isinstance(sub, Dot)]
    assert dots
