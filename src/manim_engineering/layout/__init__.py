"""Layout layer: placement, routing, spacing (no Manim, no animation)."""

from manim_engineering.layout.engine import (
    LayoutConfig,
    LayoutEngine,
    pin_world_position,
    port_world_position,
)
from manim_engineering.layout.exceptions import (
    LayoutError,
    PlacementError,
    RoutingError,
    UnknownElementError,
)
from manim_engineering.layout.grid import layout_bbox, occupancy_ratio, place_on_grid, scene_bbox
from manim_engineering.layout.routing import (
    merge_routing_hints,
    points_to_segments,
    route_orthogonal,
)
from manim_engineering.layout.types import (
    DEFAULT_NOMINAL_FRAME,
    OCCUPANCY_TARGET_MAX,
    OCCUPANCY_TARGET_MIN,
    ComponentPlacement,
    LayoutBBox,
    LayoutResult,
    Point2D,
    Segment,
    WirePath,
)

__all__ = [
    "DEFAULT_NOMINAL_FRAME",
    "OCCUPANCY_TARGET_MAX",
    "OCCUPANCY_TARGET_MIN",
    "ComponentPlacement",
    "LayoutBBox",
    "LayoutConfig",
    "LayoutEngine",
    "LayoutError",
    "LayoutResult",
    "PlacementError",
    "Point2D",
    "RoutingError",
    "Segment",
    "UnknownElementError",
    "WirePath",
    "layout_bbox",
    "scene_bbox",
    "merge_routing_hints",
    "occupancy_ratio",
    "pin_world_position",
    "port_world_position",
    "place_on_grid",
    "points_to_segments",
    "route_orthogonal",
]
