"""Component orientation transform tests."""

from __future__ import annotations

import pytest

from manim_engineering.components import OpAmp, Resistor
from manim_engineering.layout import (
    LayoutEngine,
    origin_for_pin_at,
    oriented_footprint,
    pin_world_position,
)
from manim_engineering.layout.types import ComponentOrientation, ComponentPlacement, Point2D


def test_resistor_rotate_90_swaps_footprint_dimensions() -> None:
    r = Resistor("r1")
    nominal = r.get_bounds()
    aabb, _offset = oriented_footprint(nominal, ComponentOrientation(rotation=90))
    assert aabb.width == pytest.approx(nominal.height)
    assert aabb.height == pytest.approx(nominal.width)


def test_pin_world_position_matches_origin_for_pin_at_with_rotation() -> None:
    r = Resistor("r1")
    orientation = ComponentOrientation(rotation=90)
    target = Point2D(1.5, 2.0)
    origin = origin_for_pin_at(r, "a", target, orientation=orientation)
    nominal = r.get_bounds()
    aabb, _ = oriented_footprint(nominal, orientation)
    placement = ComponentPlacement("r1", origin, aabb, orientation=orientation)
    assert pin_world_position(placement, r, "a") == target


def test_flip_y_swaps_opamp_input_pin_heights() -> None:
    op = OpAmp("op1")
    nominal = op.get_bounds()
    orientation = ComponentOrientation(flip_y=True)
    origin = Point2D(0.0, 0.0)
    aabb, _ = oriented_footprint(nominal, orientation)
    placement = ComponentPlacement("op1", origin, aabb, orientation=orientation)
    in_p = pin_world_position(placement, op, "in_p")
    in_n = pin_world_position(placement, op, "in_n")
    assert in_p.y < in_n.y


def test_layout_engine_accepts_orientation_overrides() -> None:
    from manim_engineering.core import CircuitGraph

    graph = CircuitGraph()
    r = Resistor("r1", label="R1")
    r.attach_to(graph)
    orientation = ComponentOrientation(rotation=90)
    layout = LayoutEngine().layout(
        graph,
        {"r1": r},
        placement_overrides={"r1": Point2D(0.0, 0.0)},
        orientation_overrides={"r1": orientation},
    )
    placement = layout.placements[0]
    assert placement.orientation == orientation
    assert placement.bounds.height == pytest.approx(r.get_bounds().width)


def test_layout_engine_applies_orientation_to_grid_placements() -> None:
    from manim_engineering.core import CircuitGraph

    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    orientation = ComponentOrientation(rotation=90)
    layout = LayoutEngine().layout(
        graph,
        {"r1": r1, "r2": r2},
        orientation_overrides={"r2": orientation},
    )
    placement = next(p for p in layout.placements if p.element_id == "r2")
    assert placement.orientation == orientation
    assert placement.bounds.width == pytest.approx(r2.get_bounds().height)


def test_invalid_rotation_raises() -> None:
    with pytest.raises(ValueError, match="rotation must be"):
        ComponentOrientation(rotation=45)
