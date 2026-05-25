"""Layout layer: placement, routing, spacing (no Manim, no animation)."""

from manim_engineering.layout.align import origin_for_pin_at
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
from manim_engineering.layout.footprint import assert_wires_avoid_footprints, wires_avoid_footprints
from manim_engineering.layout.grid import (
    layout_bbox,
    occupancy_ratio,
    place_on_grid,
    place_on_grid_semantic,
    scene_bbox,
)
from manim_engineering.layout.nets import (
    collect_junction_nodes,
    connection_for_wire,
    group_connections_into_nets,
    net_id_for_pins,
    route_nets,
)
from manim_engineering.layout.orientation import oriented_footprint
from manim_engineering.layout.placement import placement_order_for_graph
from manim_engineering.layout.routing import (
    ensure_visible_connection,
    merge_routing_hints,
    points_to_segments,
    route_orthogonal,
    route_through_waypoints,
    segments_intersect,
    sibling_pins_to_avoid,
    stub_direction_for_connection,
)
from manim_engineering.layout.types import (
    DEFAULT_NOMINAL_FRAME,
    MIN_VISIBLE_STUB,
    OCCUPANCY_TARGET_MAX,
    OCCUPANCY_TARGET_MIN,
    ComponentOrientation,
    ComponentPlacement,
    LayoutBBox,
    LayoutResult,
    Point2D,
    Segment,
    TextPlacementOverride,
    WirePath,
)

__all__ = [
    "DEFAULT_NOMINAL_FRAME",
    "MIN_VISIBLE_STUB",
    "OCCUPANCY_TARGET_MAX",
    "OCCUPANCY_TARGET_MIN",
    "ComponentPlacement",
    "ComponentOrientation",
    "LayoutBBox",
    "LayoutConfig",
    "LayoutEngine",
    "assert_wires_avoid_footprints",
    "collect_junction_nodes",
    "ensure_visible_connection",
    "LayoutError",
    "LayoutResult",
    "PlacementError",
    "Point2D",
    "RoutingError",
    "Segment",
    "TextPlacementOverride",
    "UnknownElementError",
    "WirePath",
    "layout_bbox",
    "scene_bbox",
    "merge_routing_hints",
    "net_id_for_pins",
    "group_connections_into_nets",
    "route_nets",
    "occupancy_ratio",
    "oriented_footprint",
    "origin_for_pin_at",
    "pin_world_position",
    "port_world_position",
    "place_on_grid",
    "place_on_grid_semantic",
    "placement_order_for_graph",
    "points_to_segments",
    "route_orthogonal",
    "route_through_waypoints",
    "segments_intersect",
    "stub_direction_for_connection",
    "wires_avoid_footprints",
]
