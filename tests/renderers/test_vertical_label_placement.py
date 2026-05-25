"""Vertical component_label auto side-picking and manual overrides."""

from __future__ import annotations

import pytest

from manim_engineering.components import Resistor, ZenerDiode
from manim_engineering.layout.orientation import oriented_footprint
from manim_engineering.layout.types import (
    DEFAULT_NOMINAL_FRAME,
    ComponentOrientation,
    ComponentPlacement,
    LabelPlacementMode,
    LayoutBBox,
    LayoutResult,
    Point2D,
    TextPlacementOverride,
)
from manim_engineering.renderers.minimal.labels import iter_label_roots, label_role
from manim_engineering.renderers.minimal.renderer import MinimalRenderer
from manim_engineering.renderers.minimal.text_placement import (
    TextRelativeSlot,
    footprint_world_rect,
    pick_vertical_label_side,
)


def _empty_layout_result(*placements: ComponentPlacement) -> LayoutResult:
    bbox = LayoutBBox(min_x=0.0, min_y=0.0, max_x=2.0, max_y=2.0)
    return LayoutResult(
        placements=placements,
        pin_positions={},
        wires=(),
        frame=DEFAULT_NOMINAL_FRAME,
        occupancy_ratio=0.5,
        layout_bbox=bbox,
        scene_bbox=bbox,
    )


def _oriented_placement(
    element_id: str,
    origin: Point2D,
    element,
    orientation: ComponentOrientation,
    **kwargs,
) -> ComponentPlacement:
    oriented_bounds, _ = oriented_footprint(element.get_bounds(), orientation)
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


def test_auto_picks_left_when_neighbor_on_right() -> None:
    rs = Resistor("rs1", label="Rs")
    neighbor = Resistor("n1")
    orientation = ComponentOrientation(rotation=90)
    rs_placement = _oriented_placement("rs1", Point2D(0.0, 0.0), rs, orientation)
    neighbor_placement = ComponentPlacement("n1", Point2D(0.5, 0.0), neighbor.get_bounds())
    layout = _empty_layout_result(rs_placement, neighbor_placement)
    assert pick_vertical_label_side(rs_placement, rs, layout) is TextRelativeSlot.LEFT_MID


def test_auto_picks_right_when_neighbor_on_left() -> None:
    rs = Resistor("rs1", label="Rs")
    neighbor = Resistor("n1")
    orientation = ComponentOrientation(rotation=90)
    rs_placement = _oriented_placement("rs1", Point2D(1.0, 0.0), rs, orientation)
    neighbor_placement = ComponentPlacement("n0", Point2D(0.0, 0.0), neighbor.get_bounds())
    layout = _empty_layout_result(neighbor_placement, rs_placement)
    assert pick_vertical_label_side(rs_placement, rs, layout) is TextRelativeSlot.RIGHT_MID


def test_manual_text_override_beats_auto_side() -> None:
    rs = Resistor("rs1", label="Rs")
    orientation = ComponentOrientation(rotation=90)
    manual = Point2D(4.0, 5.0)
    placement = _oriented_placement(
        "rs1",
        Point2D(0.0, 0.0),
        rs,
        orientation,
        text_overrides=(TextPlacementOverride(role="component_label", world=manual),),
    )
    neighbor = ComponentPlacement("n1", Point2D(0.5, 0.0), Resistor("n1").get_bounds())
    layout = _empty_layout_result(placement, neighbor)
    placed = MinimalRenderer()._place_component(
        MinimalRenderer().render(rs),
        placement,
        rs,
        layout=layout,
    )
    label = _label_by_role(placed, "component_label")
    assert float(label.get_center()[0]) == pytest.approx(manual.x)
    assert float(label.get_center()[1]) == pytest.approx(manual.y)


def test_slot_only_keeps_type_slot_for_vertical_resistor() -> None:
    rs = Resistor("rs1", label="Rs")
    orientation = ComponentOrientation(rotation=90)
    placement = _oriented_placement(
        "rs1",
        Point2D(0.0, 0.0),
        rs,
        orientation,
        label_mode=LabelPlacementMode.SLOT_ONLY,
    )
    layout = _empty_layout_result(placement)
    placed = MinimalRenderer()._place_component(
        MinimalRenderer().render(rs),
        placement,
        rs,
        layout=layout,
    )
    label = _label_by_role(placed, "component_label")
    _min_x, _min_y, _max_x, max_y = footprint_world_rect(placement)
    assert float(label.get_center()[1]) > max_y


def test_horizontal_resistor_stays_above_with_auto() -> None:
    rs = Resistor("rs1", label="Rs")
    placement = ComponentPlacement("rs1", Point2D(0.0, 0.0), rs.get_bounds())
    layout = _empty_layout_result(placement)
    placed = MinimalRenderer()._place_component(
        MinimalRenderer().render(rs),
        placement,
        rs,
        layout=layout,
    )
    label = _label_by_role(placed, "component_label")
    _min_x, _min_y, _max_x, max_y = footprint_world_rect(placement)
    assert float(label.get_center()[1]) > max_y


def test_zener_fixture_vertical_labels_on_left() -> None:
    import importlib.util
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "fixture", repo / "examples/analog/07_zener_regulator.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _graph, elements, layout = mod.build_zener_regulator_fixture()
    renderer = MinimalRenderer()
    mob = renderer.render_circuit(_graph, layout, elements)
    rs_placement = next(item for item in layout.placements if item.element_id == "rs1")
    zd_placement = next(item for item in layout.placements if item.element_id == "zd1")
    rs_min_x, rs_min_y, _, rs_max_y = footprint_world_rect(rs_placement)
    zd_min_x, zd_min_y, _, zd_max_y = footprint_world_rect(zd_placement)
    labels = [
        label
        for label in iter_label_roots(mob)
        if label_role(label) == "component_label"
    ]
    assert len(labels) == 5
    rs_label = next(label for label in labels if label.text == "Rs")
    dz_label = next(label for label in labels if label.text == "Dz")
    assert float(rs_label.get_center()[0]) < rs_min_x
    assert float(dz_label.get_center()[0]) < zd_min_x
