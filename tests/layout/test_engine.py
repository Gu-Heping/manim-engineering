"""LayoutEngine integration tests with CircuitGraph."""

from __future__ import annotations

import pytest

from manim_engineering.components import Resistor
from manim_engineering.layout import (
    OCCUPANCY_TARGET_MAX,
    OCCUPANCY_TARGET_MIN,
    LayoutConfig,
    LayoutEngine,
    UnknownElementError,
)
from manim_engineering.layout.types import DEFAULT_NOMINAL_FRAME, Point2D
from manim_engineering.core import CircuitGraph


def _two_resistor_graph() -> tuple[CircuitGraph, Resistor, Resistor]:

    graph = CircuitGraph()

    r1 = Resistor("r1", label="R1")

    r2 = Resistor("r2", label="R2")

    r1.attach_to(graph)

    r2.attach_to(graph)

    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    return graph, r1, r2


def test_layout_engine_deterministic() -> None:

    graph, r1, r2 = _two_resistor_graph()

    engine = LayoutEngine()

    elements = {"r1": r1, "r2": r2}

    first = engine.layout(graph, elements)

    second = engine.layout(graph, elements)

    assert first.placements == second.placements

    assert first.pin_positions == second.pin_positions

    assert first.wires == second.wires


def test_layout_routes_between_pin_positions() -> None:

    graph, r1, r2 = _two_resistor_graph()

    result = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})

    assert len(result.wires) == 1

    wire = result.wires[0]

    assert wire.points[0] == result.pin_positions["r1.b"]

    assert wire.points[-1] == result.pin_positions["r2.a"]

    for segment in wire.segments:
        assert segment.start.x == segment.end.x or segment.start.y == segment.end.y


def test_layout_wire_does_not_use_bounds_overlap_heuristic() -> None:
    """Routing keys off pin world positions, not component bbox intersection."""

    graph, r1, r2 = _two_resistor_graph()

    result = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})

    wire = result.wires[0]

    assert wire.points[0].y == wire.points[-1].y

    assert wire.points[0].x < wire.points[-1].x


def test_layout_occupancy_documented_for_fixture() -> None:

    graph, r1, r2 = _two_resistor_graph()

    result = LayoutEngine(LayoutConfig(nominal_frame=DEFAULT_NOMINAL_FRAME)).layout(
        graph, {"r1": r1, "r2": r2}
    )

    assert OCCUPANCY_TARGET_MIN <= result.occupancy_ratio <= OCCUPANCY_TARGET_MAX


def test_unknown_element_raises() -> None:

    graph, r1, _r2 = _two_resistor_graph()

    with pytest.raises(UnknownElementError):
        LayoutEngine().layout(graph, {"r1": r1})


def test_layout_full_override_skips_grid() -> None:
    """Every element gets its origin from the override map; grid is never used."""

    graph, r1, r2 = _two_resistor_graph()

    overrides = {
        "r1": Point2D(0.0, 0.0),
        "r2": Point2D(2.5, 1.75),
    }

    result = LayoutEngine().layout(
        graph,
        {"r1": r1, "r2": r2},
        placement_overrides=overrides,
    )

    by_id = {p.element_id: p for p in result.placements}
    assert by_id["r1"].origin == Point2D(0.0, 0.0)
    assert by_id["r2"].origin == Point2D(2.5, 1.75)
    assert by_id["r1"].bounds == r1.get_bounds()
    assert by_id["r2"].bounds == r2.get_bounds()
    assert len(result.wires) == 1


def test_layout_partial_override_mixes_grid() -> None:
    """Unmapped elements still flow through place_on_grid; mapped ones do not."""

    graph, r1, r2 = _two_resistor_graph()

    overrides = {"r2": Point2D(3.5, 2.0)}

    result = LayoutEngine().layout(
        graph,
        {"r1": r1, "r2": r2},
        placement_overrides=overrides,
    )

    by_id = {p.element_id: p for p in result.placements}
    assert by_id["r2"].origin == Point2D(3.5, 2.0)
    assert by_id["r1"].origin.x == 0.0
    assert len(result.wires) == 1
    wire = result.wires[0]
    assert wire.points[0] == result.pin_positions["r1.b"]
    assert wire.points[-1] == result.pin_positions["r2.a"]


def test_layout_override_unknown_element_id_raises() -> None:

    graph, r1, r2 = _two_resistor_graph()

    with pytest.raises(UnknownElementError):
        LayoutEngine().layout(
            graph,
            {"r1": r1, "r2": r2},
            placement_overrides={"ghost": Point2D(0.0, 0.0)},
        )
