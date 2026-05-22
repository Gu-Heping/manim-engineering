"""Wire path helpers: layout geometry without semantic mutation."""

from __future__ import annotations

import numpy as np
from manim import VMobject

from manim_engineering.layout.types import LayoutResult, Point2D, WirePath
from manim_engineering.semantic.graph import CircuitGraph


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
    """Order polyline points from source pin toward sink pin."""
    points = wire.points
    if len(points) < 2:
        return points

    start = layout.pin_positions[from_pin_id]
    end = layout.pin_positions[to_pin_id]

    def dist2(a: Point2D, b: Point2D) -> float:
        return (a.x - b.x) ** 2 + (a.y - b.y) ** 2

    if dist2(points[0], end) < dist2(points[0], start):
        return tuple(reversed(points))
    return points


def path_mobject_from_points(points: tuple[Point2D, ...]) -> VMobject:
    """Build a Manim path through layout/world coordinates."""
    path = VMobject()
    corners = [[point.x, point.y, 0.0] for point in points]
    path.set_points_as_corners(corners)
    return path


def point3_array(point: Point2D) -> np.ndarray:
    return np.array([point.x, point.y, 0.0], dtype=float)
