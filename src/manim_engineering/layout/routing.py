"""Orthogonal wire routing from pin world positions and routing hints."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Literal

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.connection import Connection
from manim_engineering.layout.footprint import segment_crosses_footprint_interior
from manim_engineering.layout.types import (
    MIN_VISIBLE_STUB,
    ComponentPlacement,
    Point2D,
    Segment,
)

_PIN_AVOID_EPS = 1e-6
_COORD_EPS = 1e-6

StubDirection = Literal["+x", "-x", "+y", "-y"]
_ALL_STUB_DIRECTIONS: tuple[StubDirection, ...] = ("+x", "-x", "+y", "-y")


def _points_close(left: Point2D, right: Point2D) -> bool:
    return abs(left.x - right.x) <= _COORD_EPS and abs(left.y - right.y) <= _COORD_EPS


def _dedupe_collinear(points: list[Point2D]) -> tuple[Point2D, ...]:
    """Remove consecutive duplicates and collinear middle vertices."""

    if not points:
        return ()

    cleaned: list[Point2D] = [points[0]]
    for point in points[1:]:
        if _points_close(point, cleaned[-1]):
            continue
        cleaned.append(point)

    if len(cleaned) < 3:
        return tuple(cleaned)

    simplified: list[Point2D] = [cleaned[0]]
    for index in range(1, len(cleaned) - 1):
        prev_pt = simplified[-1]
        mid = cleaned[index]
        next_pt = cleaned[index + 1]
        if prev_pt.x == mid.x == next_pt.x or prev_pt.y == mid.y == next_pt.y:
            continue
        simplified.append(mid)
    simplified.append(cleaned[-1])
    return tuple(simplified)


def _prefer_horizontal_first(hints: tuple[str, ...]) -> bool:
    """Choose routing bend order from pin/component routing hints."""

    hint_set = {hint.lower() for hint in hints}

    # Mixed horizontal + vertical (e.g. resistor → NMOS drain): route vertical
    # first so the bend does not cut through the channel at gate height.
    if "horizontal" in hint_set and "vertical" in hint_set:
        if "up" in hint_set or "down" in hint_set:
            return False

    if "horizontal" in hint_set:
        return True

    if "vertical" in hint_set or "down" in hint_set or "up" in hint_set:
        return False

    return True


def _vertical_segment_passes_point(
    x: float,
    y0: float,
    y1: float,
    point: Point2D,
) -> bool:
    lo, hi = sorted((y0, y1))
    return (
        abs(point.x - x) <= _PIN_AVOID_EPS
        and lo + _PIN_AVOID_EPS < point.y < hi - _PIN_AVOID_EPS
    )


def _horizontal_segment_passes_point(
    x0: float,
    x1: float,
    y: float,
    point: Point2D,
) -> bool:
    lo, hi = sorted((x0, x1))
    return (
        abs(point.y - y) <= _PIN_AVOID_EPS
        and lo + _PIN_AVOID_EPS < point.x < hi - _PIN_AVOID_EPS
    )


def _route_crosses_avoid_points(
    start: Point2D,
    corner: Point2D,
    end: Point2D,
    avoid_points: tuple[Point2D, ...],
) -> bool:
    for point in avoid_points:
        if start.x == corner.x == end.x:
            if _vertical_segment_passes_point(start.x, start.y, end.y, point):
                return True
        elif start.y == corner.y == end.y:
            if _horizontal_segment_passes_point(start.x, end.x, start.y, point):
                return True
        else:
            if _vertical_segment_passes_point(start.x, start.y, corner.y, point):
                return True
            if _horizontal_segment_passes_point(corner.x, end.x, corner.y, point):
                return True
    return False


def route_orthogonal(
    start: Point2D,
    end: Point2D,
    *,
    hints: tuple[str, ...] = (),
    avoid_points: tuple[Point2D, ...] = (),
) -> tuple[Point2D, ...]:
    """Build an orthogonal polyline between ``start`` and ``end``.

    Default bend order follows layout rules: horizontal segment first (left→right
    signal flow), unless hints request vertical-first routing. When the preferred
    bend would pass through ``avoid_points`` (e.g. sibling pins on the same
    component), the bend order is flipped.
    """

    if start == end:
        return (start,)

    if start.x == end.x or start.y == end.y:
        return _dedupe_collinear([start, end])

    horizontal_first = _prefer_horizontal_first(hints)
    if horizontal_first:
        corner = Point2D(end.x, start.y)
    else:
        corner = Point2D(start.x, end.y)

    if avoid_points and _route_crosses_avoid_points(start, corner, end, avoid_points):
        if horizontal_first:
            corner = Point2D(start.x, end.y)
        else:
            corner = Point2D(end.x, start.y)

    return _dedupe_collinear([start, corner, end])


def route_through_waypoints(
    start: Point2D,
    end: Point2D,
    waypoints: Sequence[Point2D],
    *,
    hints: tuple[str, ...] = (),
    avoid_points: tuple[Point2D, ...] = (),
) -> tuple[Point2D, ...]:
    """Orthogonal route visiting intermediate waypoints in order."""
    if _points_close(start, end) and waypoints:
        merged: list[Point2D] = [start]
        for waypoint in waypoints:
            leg = route_orthogonal(
                merged[-1],
                waypoint,
                hints=hints,
                avoid_points=avoid_points,
            )
            merged.extend(leg[1:])
        return _dedupe_collinear(merged)

    chain = (start, *waypoints, end)
    merged: list[Point2D] = [chain[0]]
    for index in range(len(chain) - 1):
        leg = route_orthogonal(
            chain[index],
            chain[index + 1],
            hints=hints,
            avoid_points=avoid_points,
        )
        merged.extend(leg[1:])
    return _dedupe_collinear(merged)


def segments_intersect(
    left: Segment,
    right: Segment,
    *,
    exclude_endpoints: bool = True,
) -> bool:
    """True when two axis-aligned segments cross at an interior point."""
    if left.start.x == left.end.x and right.start.x == right.end.x:
        if abs(left.start.x - right.start.x) > _COORD_EPS:
            return False
        lo_a, hi_a = sorted((left.start.y, left.end.y))
        lo_b, hi_b = sorted((right.start.y, right.end.y))
        overlap_lo = max(lo_a, lo_b)
        overlap_hi = min(hi_a, hi_b)
        if overlap_hi - overlap_lo <= _COORD_EPS:
            return False
        if exclude_endpoints:
            return overlap_hi - overlap_lo > 2 * _COORD_EPS
        return True

    if left.start.y == left.end.y and right.start.y == right.end.y:
        if abs(left.start.y - right.start.y) > _COORD_EPS:
            return False
        lo_a, hi_a = sorted((left.start.x, left.end.x))
        lo_b, hi_b = sorted((right.start.x, right.end.x))
        overlap_lo = max(lo_a, lo_b)
        overlap_hi = min(hi_a, hi_b)
        if overlap_hi - overlap_lo <= _COORD_EPS:
            return False
        if exclude_endpoints:
            return overlap_hi - overlap_lo > 2 * _COORD_EPS
        return True

    vertical = left if left.start.x == left.end.x else right
    horizontal = right if vertical is left else left
    if vertical.start.x != vertical.end.x or horizontal.start.y != horizontal.end.y:
        return False

    vx = vertical.start.x
    vy0, vy1 = sorted((vertical.start.y, vertical.end.y))
    hy = horizontal.start.y
    hx0, hx1 = sorted((horizontal.start.x, horizontal.end.x))

    if not (hx0 < vx < hx1 and vy0 < hy < vy1):
        return False
    if exclude_endpoints:
        return (
            vx - hx0 > _COORD_EPS
            and hx1 - vx > _COORD_EPS
            and hy - vy0 > _COORD_EPS
            and vy1 - hy > _COORD_EPS
        )
    return True


def points_to_segments(points: tuple[Point2D, ...]) -> tuple[Segment, ...]:
    """Convert a polyline into axis-aligned segments (drops zero-length legs)."""

    if len(points) < 2:
        return ()

    segments: list[Segment] = []
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        if _points_close(start, end):
            continue
        segments.append(Segment(start, end))
    return tuple(segments)


def merge_routing_hints(*hint_groups: tuple[str, ...]) -> tuple[str, ...]:
    """Merge hint tuples deterministically (sorted unique)."""

    merged = sorted({hint for group in hint_groups for hint in group})

    return tuple(merged)


def sibling_pins_to_avoid(
    connection,
    pin_positions: Mapping[str, Point2D],
    elements: Mapping[str, CircuitElement],
) -> tuple[Point2D, ...]:
    """Other pins on connection endpoints — routes must not pass through them."""
    avoid: list[Point2D] = []
    for port in (connection.port_a, connection.port_b):
        element = elements[port.owner_id]
        for pin_name in element.pins:
            pin = element.get_pin(pin_name)
            if pin.id == port.id:
                continue
            avoid.append(pin_positions[pin.id])
    return tuple(avoid)


def _stub_endpoint(origin: Point2D, direction: StubDirection, length: float) -> Point2D:
    if direction == "+x":
        return Point2D(origin.x + length, origin.y)
    if direction == "-x":
        return Point2D(origin.x - length, origin.y)
    if direction == "+y":
        return Point2D(origin.x, origin.y + length)
    return Point2D(origin.x, origin.y - length)


def _stub_candidate_directions(
    hints: tuple[str, ...],
    *,
    coincident: bool = False,
) -> tuple[StubDirection, ...]:
    hint_set = {hint.lower() for hint in hints}
    if coincident and "horizontal" in hint_set:
        return ("-x", "+x")
    if coincident and ("vertical" in hint_set or "up" in hint_set or "down" in hint_set):
        if "down" in hint_set and "up" not in hint_set:
            return ("-y", "+y")
        if "up" in hint_set and "down" not in hint_set:
            return ("+y", "-y")
        return ("+y", "-y")
    if _prefer_horizontal_first(hints):
        return ("+x", "-x")
    if "down" in hint_set and "up" not in hint_set:
        return ("-y", "+y")
    if "up" in hint_set and "down" not in hint_set:
        return ("+y", "-y")
    return ("+y", "-y")


def _stub_crosses_foreign_footprint(
    segment: Segment,
    connection: Connection,
    placements_by_id: Mapping[str, ComponentPlacement],
) -> bool:
    for element_id, placement in placements_by_id.items():
        if segment_crosses_footprint_interior(segment, placement):
            return True
    return False


def stub_direction_for_connection(
    connection: Connection,
    pin_positions: Mapping[str, Point2D],
    placements_by_id: Mapping[str, ComponentPlacement],
    *,
    hints: tuple[str, ...],
) -> StubDirection:
    """Pick a stub axis/direction that leaves the junction without crossing footprints."""
    origin = pin_positions[connection.port_a.id]
    end = pin_positions[connection.port_b.id]
    coincident = _points_close(origin, end)
    candidates = _stub_candidate_directions(hints, coincident=coincident)
    for direction in candidates:
        segment = Segment(origin, _stub_endpoint(origin, direction, MIN_VISIBLE_STUB))
        if not _stub_crosses_foreign_footprint(segment, connection, placements_by_id):
            return direction
    for direction in _ALL_STUB_DIRECTIONS:
        if direction in candidates:
            continue
        segment = Segment(origin, _stub_endpoint(origin, direction, MIN_VISIBLE_STUB))
        if not _stub_crosses_foreign_footprint(segment, connection, placements_by_id):
            return direction
    return candidates[0]


def ensure_visible_connection(
    points: tuple[Point2D, ...],
    *,
    connection: Connection,
    pin_positions: Mapping[str, Point2D],
    placements_by_id: Mapping[str, ComponentPlacement],
    hints: tuple[str, ...],
    min_stub: float = MIN_VISIBLE_STUB,
) -> tuple[Point2D, ...]:
    """Expand coincident pin routes into a minimum visible orthogonal stub."""
    if not points:
        return points
    if len(points) >= 2 and not _points_close(points[0], points[-1]):
        return points

    origin = points[0]
    direction = stub_direction_for_connection(
        connection,
        pin_positions,
        placements_by_id,
        hints=hints,
    )
    end = _stub_endpoint(origin, direction, min_stub)
    return _dedupe_collinear([origin, end])
