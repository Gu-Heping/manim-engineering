"""Renderer placement must match layout orientation transforms."""

from __future__ import annotations

import pytest

from manim import UL, UR

from manim_engineering.components import OpAmp, Resistor
from manim_engineering.layout.engine import pin_world_position
from manim_engineering.layout.orientation import oriented_footprint
from manim_engineering.layout.types import ComponentOrientation, ComponentPlacement, LabelPlacementMode, Point2D
from manim_engineering.renderers.minimal.labels import iter_label_roots, label_role
from manim_engineering.renderers.minimal.renderer import MinimalRenderer


def _oriented_placement(
    element_id: str,
    origin: Point2D,
    element,
    orientation: ComponentOrientation,
    **kwargs,
) -> ComponentPlacement:
    nominal = element.get_bounds()
    oriented_bounds, _ = oriented_footprint(nominal, orientation)
    return ComponentPlacement(
        element_id,
        origin,
        oriented_bounds,
        orientation=orientation,
        **kwargs,
    )


def _label_by_role(placed: object, role: str):
    for label in iter_label_roots(placed):
        if label_role(label) == role:
            return label
    raise AssertionError(f"no label with role {role!r}")


def _pin_dot_positions(renderer: MinimalRenderer, element, placement) -> dict[str, tuple[float, float]]:
    from manim_engineering.renderers.minimal.text_placement import detach_label_roots

    mob = renderer.render(element)
    geometry_only, _ = detach_label_roots(mob)
    placed = renderer._place_geometry_at(geometry_only, placement, element.get_bounds())
    dots = placed.submobjects[1]
    names = sorted(name for name in element.anchor_points if name != "center")
    return {
        name: (dot.get_center()[0], dot.get_center()[1])
        for name, dot in zip(names, dots.submobjects, strict=True)
    }


def _assert_labels_upright(placed: object) -> None:
    for label in iter_label_roots(placed):
        ul = label.get_corner(UL)
        ur = label.get_corner(UR)
        assert float(ul[0]) < float(ur[0])


def test_flip_y_keeps_opamp_pointing_right() -> None:
    op = OpAmp("op1")
    bounds = op.get_bounds()
    orientation = ComponentOrientation(flip_y=True)
    placement = ComponentPlacement("op1", Point2D(0.0, 0.0), bounds, orientation=orientation)
    renderer = MinimalRenderer()
    placed = renderer._place_component(renderer.render(op), placement, op)
    symbol_body = placed.submobjects[0].submobjects[0]
    triangle = symbol_body.submobjects[0]
    xs = triangle.get_vertices()[:, 0]
    assert max(xs) > min(xs) + 0.5
    assert max(xs) == pytest.approx(bounds.width * 0.85, rel=0.05)
    _assert_labels_upright(placed)


def test_flip_y_opamp_labels_stay_upright() -> None:
    op = OpAmp("op1", label="A1")
    orientation = ComponentOrientation(flip_y=True)
    placement = ComponentPlacement(
        "op1",
        Point2D(0.5, 0.0),
        op.get_bounds(),
        orientation=orientation,
    )
    placed = MinimalRenderer()._place_component(MinimalRenderer().render(op), placement, op)
    _assert_labels_upright(placed)


def test_rotation_90_resistor_label_stays_upright() -> None:
    resistor = Resistor("r1", label="R1")
    orientation = ComponentOrientation(rotation=90)
    placement = ComponentPlacement(
        "r1",
        Point2D(0.0, 0.0),
        resistor.get_bounds(),
        orientation=orientation,
    )
    placed = MinimalRenderer()._place_component(
        MinimalRenderer().render(resistor),
        placement,
        resistor,
    )
    _assert_labels_upright(placed)


def test_renderer_pin_dots_match_layout_flip_y() -> None:
    op = OpAmp("op1")
    orientation = ComponentOrientation(flip_y=True)
    origin = Point2D(0.5, 0.0)
    placement = ComponentPlacement("op1", origin, op.get_bounds(), orientation=orientation)
    renderer = MinimalRenderer()
    rendered = _pin_dot_positions(renderer, op, placement)
    for pin_name in ("in_p", "in_n", "out"):
        layout_pt = pin_world_position(placement, op, pin_name)
        rx, ry = rendered[pin_name]
        assert rx == pytest.approx(layout_pt.x)
        assert ry == pytest.approx(layout_pt.y)


def test_flip_y_opamp_component_label_stays_below() -> None:
    op = OpAmp("op1", label="A1")
    orientation = ComponentOrientation(flip_y=True)
    placement = _oriented_placement("op1", Point2D(0.5, 0.0), op, orientation)
    placed = MinimalRenderer()._place_component(MinimalRenderer().render(op), placement, op)
    label = _label_by_role(placed, "component_label")
    mid_y = placement.origin.y + placement.bounds.height * 0.5
    assert float(label.get_center()[1]) < mid_y
    _assert_labels_upright(placed)


def test_rotation_90_resistor_label_stays_above_in_slot_only_mode() -> None:
    resistor = Resistor("r1", label="R1")
    orientation = ComponentOrientation(rotation=90)
    placement = _oriented_placement(
        "r1",
        Point2D(0.0, 0.0),
        resistor,
        orientation,
        label_mode=LabelPlacementMode.SLOT_ONLY,
    )
    placed = MinimalRenderer()._place_component(
        MinimalRenderer().render(resistor),
        placement,
        resistor,
    )
    label = _label_by_role(placed, "component_label")
    top_y = placement.origin.y + placement.bounds.height
    assert float(label.get_center()[1]) > top_y
    _assert_labels_upright(placed)


def test_flip_y_opamp_plus_minus_near_pins() -> None:
    op = OpAmp("op1")
    orientation = ComponentOrientation(flip_y=True)
    placement = _oriented_placement("op1", Point2D(0.5, 0.0), op, orientation)
    placed = MinimalRenderer()._place_component(MinimalRenderer().render(op), placement, op)
    plus = _label_by_role(placed, "opamp.plus")
    minus = _label_by_role(placed, "opamp.minus")
    in_p = pin_world_position(placement, op, "in_p")
    in_n = pin_world_position(placement, op, "in_n")
    width = op.get_bounds().width
    assert float(plus.get_center()[0]) == pytest.approx(in_p.x + 0.32 * width, rel=0.05)
    assert float(plus.get_center()[1]) == pytest.approx(in_p.y, rel=0.05)
    assert float(minus.get_center()[0]) == pytest.approx(in_n.x + 0.32 * width, rel=0.05)
    assert float(minus.get_center()[1]) == pytest.approx(in_n.y, rel=0.05)
    _assert_labels_upright(placed)


def test_renderer_pin_dots_match_layout_flip_x() -> None:
    r = Resistor("r1")
    orientation = ComponentOrientation(flip_x=True)
    origin = Point2D(1.0, 0.5)
    placement = ComponentPlacement("r1", origin, r.get_bounds(), orientation=orientation)
    renderer = MinimalRenderer()
    rendered = _pin_dot_positions(renderer, r, placement)
    for pin_name in ("a", "b"):
        layout_pt = pin_world_position(placement, r, pin_name)
        rx, ry = rendered[pin_name]
        assert rx == pytest.approx(layout_pt.x)
        assert ry == pytest.approx(layout_pt.y)
