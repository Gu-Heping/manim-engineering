"""Wire path helpers: layout geometry without semantic mutation."""

from __future__ import annotations

import numpy as np
from manim import VMobject

from manim_engineering.layout.types import LayoutResult, Point2D, WirePath
from manim_engineering.core.graph import CircuitGraph


def connection_id_for_pins(
    graph: CircuitGraph,
    from_pin_id: str,
    to_pin_id: str,
) -> str:
    """Resolve the connection id for a pin pair in the topology."""
    target = {from_pin_id, to_pin_id}
    for connection in graph.connections:
        if {connection.pin_a.id, connection.pin_b.id} == target:
            return connection.id
    msg = f"no connection between pins {from_pin_id!r} and {to_pin_id!r}"
    raise ValueError(msg)


def wire_path_for_connection(layout: LayoutResult, connection_id: str) -> WirePath:
    """Return the routed wire path for a connection id."""
    for wire in layout.wires:
        if wire.connection_id == connection_id:
            return wire
    msg = f"no routed wire for connection {connection_id!r}"
    raise ValueError(msg)


def oriented_wire_points(
    layout: LayoutResult,
    wire: WirePath,
    from_pin_id: str,
    to_pin_id: str,
) -> tuple[Point2D, ...]:
    """Order polyline points from source pin toward sink pin, trimmed to pin span."""
    points = wire.points
    if len(points) < 2:
        return points

    start = layout.pin_positions[from_pin_id]
    end = layout.pin_positions[to_pin_id]

    def dist2(a: Point2D, b: Point2D) -> float:
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

    if dist2(points[0], end) < dist2(points[0], start):
        ordered = tuple(reversed(points))
    else:
        ordered = points

    return trim_points_between_pins(layout, ordered, from_pin_id, to_pin_id)


def trim_points_between_pins(
    layout: LayoutResult,
    points: tuple[Point2D, ...],
    from_pin_id: str,
    to_pin_id: str,
) -> tuple[Point2D, ...]:
    """Keep only the polyline span between pin anchors (pulse stops at footprint edge)."""
    if len(points) < 2:
        return points

    start = layout.pin_positions[from_pin_id]
    end = layout.pin_positions[to_pin_id]

    def nearest_index(target: Point2D) -> int:
        best = 0
        best_d = float("inf")
        for index, point in enumerate(points):
            d = (point.x - target.x) ** 2 + (point.y - target.y) ** 2
            if d < best_d:
                best_d = d
                best = index
        return best

    i0 = nearest_index(start)
    i1 = nearest_index(end)
    if i0 <= i1:
        span = points[i0 : i1 + 1]
    else:
        span = points[i1 : i0 + 1][::-1]

    if not span:
        return (start, end)
    if span[0] != start:
        span = (start, *span)
    if span[-1] != end:
        span = (*span, end)
    return span


def wire_path_length(points: tuple[Point2D, ...]) -> float:
    """Total Euclidean length of a routed polyline."""
    if len(points) < 2:
        return 0.0
    total = 0.0
    for index in range(len(points) - 1):
        dx = points[index + 1].x - points[index].x
        dy = points[index + 1].y - points[index].y
        total += float(np.hypot(dx, dy))
    return total


def path_mobject_from_points(points: tuple[Point2D, ...]) -> VMobject:
    """Build a Manim path through layout/world coordinates."""
    path = VMobject()
    corners = [[point.x, point.y, 0.0] for point in points]
    path.set_points_as_corners(corners)
    return path


def point3_array(point: Point2D) -> np.ndarray:
    return np.array([point.x, point.y, 0.0], dtype=float)
