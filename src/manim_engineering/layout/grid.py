"""Deterministic grid placement from component bounds and anchors."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from manim_engineering.components.common.ground import Ground
from manim_engineering.components.common.vcc import VCC
from manim_engineering.components.element import CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.layout.types import ComponentPlacement, LayoutBBox, Point2D, WirePath

_SIGNAL_ROW = 1
_POWER_ROW = 2
_GROUND_ROW = 0


def _placement_at_row(
    element: CircuitElement,
    *,
    row: int,
    x: float,
    row_height: float,
    cell_gap: float,
) -> ComponentPlacement:
    bounds = element.get_bounds()
    y_origin = row * (row_height + cell_gap)
    pin_row_y = y_origin + row_height * 0.5
    origin_y = pin_row_y - 0.5 * bounds.height
    return ComponentPlacement(
        element_id=element.element_id,
        origin=Point2D(x, origin_y),
        bounds=bounds,
    )


def place_on_grid(
    elements: Iterable[CircuitElement],
    *,
    cell_gap: float = 0.5,
    row: int = 0,
) -> tuple[ComponentPlacement, ...]:
    """

    Place components left→right on a single row (deterministic by ``element_id``).



    Origins are bottom-left corners in world coordinates; row index only affects Y.

    """

    if cell_gap < 0:
        msg = f"cell_gap must be non-negative, got {cell_gap}"

        raise ValueError(msg)

    ordered_elements: Sequence[CircuitElement] = tuple(elements)

    if not ordered_elements:
        return ()

    row_heights = [element.get_bounds().height for element in ordered_elements]

    row_height = max(row_heights)

    y_origin = row * (row_height + cell_gap)

    placements: list[ComponentPlacement] = []

    x_cursor = 0.0

    pin_row_y = y_origin + row_height * 0.5

    for element in ordered_elements:
        bounds = element.get_bounds()
        origin_y = pin_row_y - 0.5 * bounds.height

        placements.append(
            ComponentPlacement(
                element_id=element.element_id,
                origin=Point2D(x_cursor, origin_y),
                bounds=bounds,
            )
        )

        x_cursor += bounds.width + cell_gap

    return tuple(placements)


def place_on_grid_semantic(
    elements: Iterable[CircuitElement],
    *,
    cell_gap: float = 0.5,
) -> tuple[ComponentPlacement, ...]:
    """
    Layer VCC above, GND below, and the signal chain left→right on the middle row.

    Falls back to single-row ``place_on_grid`` when no power symbols are present or
    when every element is a power symbol.
    """

    ordered: Sequence[CircuitElement] = tuple(elements)
    if not ordered:
        return ()

    vcc_elements = tuple(element for element in ordered if isinstance(element, VCC))
    gnd_elements = tuple(element for element in ordered if isinstance(element, Ground))
    signal_elements = tuple(
        element
        for element in ordered
        if element not in vcc_elements and element not in gnd_elements
    )

    if (not vcc_elements and not gnd_elements) or not signal_elements:
        return place_on_grid(ordered, cell_gap=cell_gap)

    signal_placements = place_on_grid(signal_elements, cell_gap=cell_gap, row=_SIGNAL_ROW)
    placements_by_id = {placement.element_id: placement for placement in signal_placements}

    all_elements = (*signal_elements, *vcc_elements, *gnd_elements)
    row_height = max(element.get_bounds().height for element in all_elements)

    first_signal = signal_placements[0]
    last_signal = signal_placements[-1]

    for element in vcc_elements:
        placements_by_id[element.element_id] = _placement_at_row(
            element,
            row=_POWER_ROW,
            x=first_signal.origin.x,
            row_height=row_height,
            cell_gap=cell_gap,
        )

    for element in gnd_elements:
        last_center_x = last_signal.origin.x + 0.5 * last_signal.bounds.width
        gnd_x = last_center_x - 0.5 * element.get_bounds().width
        placements_by_id[element.element_id] = _placement_at_row(
            element,
            row=_GROUND_ROW,
            x=gnd_x,
            row_height=row_height,
            cell_gap=cell_gap,
        )

    return tuple(placements_by_id[element.element_id] for element in ordered)


def layout_bbox(placements: Sequence[ComponentPlacement]) -> LayoutBBox:
    """Tight axis-aligned bbox covering all placed component footprints."""

    if not placements:
        return LayoutBBox(min_x=0.0, min_y=0.0, max_x=0.0, max_y=0.0)

    min_x = min(p.origin.x for p in placements)

    min_y = min(p.origin.y for p in placements)

    max_x = max(p.origin.x + p.bounds.width for p in placements)

    max_y = max(p.origin.y + p.bounds.height for p in placements)

    return LayoutBBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)


def scene_bbox(
    placements: Sequence[ComponentPlacement],
    wires: Sequence[WirePath],
) -> LayoutBBox:
    """Union of component footprints and all routed wire segment points."""
    bbox = layout_bbox(placements)
    if not wires:
        return bbox
    min_x, min_y, max_x, max_y = bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y
    for wire in wires:
        for point in wire.points:
            min_x = min(min_x, point.x)
            min_y = min(min_y, point.y)
            max_x = max(max_x, point.x)
            max_y = max(max_y, point.y)
    return LayoutBBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)


def occupancy_ratio(bbox: LayoutBBox, frame: Bounds) -> float:
    """Fraction of nominal frame area occupied by the layout bounding box."""

    frame_area = frame.width * frame.height

    if frame_area <= 0:
        msg = f"frame area must be positive: {frame.width}×{frame.height}"

        raise ValueError(msg)

    return bbox.area / frame_area
