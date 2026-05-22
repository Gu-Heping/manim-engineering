"""Deterministic grid placement from component bounds and anchors."""



from __future__ import annotations

from collections.abc import Iterable, Sequence

from manim_engineering.components.element import CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.layout.types import ComponentPlacement, LayoutBBox, Point2D


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



    sorted_elements: Sequence[CircuitElement] = tuple(

        sorted(elements, key=lambda element: element.element_id)

    )

    if not sorted_elements:

        return ()



    row_heights = [element.get_bounds().height for element in sorted_elements]

    row_height = max(row_heights)

    y_origin = row * (row_height + cell_gap)



    placements: list[ComponentPlacement] = []

    x_cursor = 0.0

    for element in sorted_elements:

        bounds = element.get_bounds()

        placements.append(

            ComponentPlacement(

                element_id=element.element_id,

                origin=Point2D(x_cursor, y_origin),

                bounds=bounds,

            )

        )

        x_cursor += bounds.width + cell_gap



    return tuple(placements)





def layout_bbox(placements: Sequence[ComponentPlacement]) -> LayoutBBox:

    """Tight axis-aligned bbox covering all placed component footprints."""

    if not placements:

        return LayoutBBox(min_x=0.0, min_y=0.0, max_x=0.0, max_y=0.0)



    min_x = min(p.origin.x for p in placements)

    min_y = min(p.origin.y for p in placements)

    max_x = max(p.origin.x + p.bounds.width for p in placements)

    max_y = max(p.origin.y + p.bounds.height for p in placements)

    return LayoutBBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)





def occupancy_ratio(bbox: LayoutBBox, frame: Bounds) -> float:

    """Fraction of nominal frame area occupied by the layout bounding box."""

    frame_area = frame.width * frame.height

    if frame_area <= 0:

        msg = f"frame area must be positive: {frame.width}×{frame.height}"

        raise ValueError(msg)

    return bbox.area / frame_area


