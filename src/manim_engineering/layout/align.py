"""Pin-aligned placement helpers for manual topology layouts."""

from __future__ import annotations

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.exceptions import InvalidPortError
from manim_engineering.layout.orientation import pin_local_in_aabb
from manim_engineering.layout.types import ComponentOrientation, Point2D


def origin_for_pin_at(
    element: CircuitElement,
    pin_name: str,
    target: Point2D,
    *,
    orientation: ComponentOrientation = ComponentOrientation(),
) -> Point2D:
    """Return placement origin so ``pin_name`` sits at ``target`` in world space."""
    anchors = element.anchor_points
    if pin_name not in anchors:
        raise InvalidPortError(f"no anchor for pin {element.element_id}.{pin_name}")
    anchor_x, anchor_y = anchors[pin_name]
    nominal = element.get_bounds()
    local = pin_local_in_aabb(anchor_x, anchor_y, nominal, orientation)
    return Point2D(
        target.x - local.x,
        target.y - local.y,
    )
