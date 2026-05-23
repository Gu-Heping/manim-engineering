"""Orthogonal wire routing from pin world positions and routing hints."""

from __future__ import annotations

from manim_engineering.layout.types import Point2D, Segment


def _dedupe_collinear(points: list[Point2D]) -> tuple[Point2D, ...]:
    """Remove consecutive duplicate points."""

    if not points:
        return ()

    out: list[Point2D] = [points[0]]

    for point in points[1:]:
        if point != out[-1]:
            out.append(point)

    return tuple(out)


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


def route_orthogonal(
    start: Point2D,
    end: Point2D,
    *,
    hints: tuple[str, ...] = (),
) -> tuple[Point2D, ...]:
    """

    Build an orthogonal polyline between ``start`` and ``end``.



    Default bend order follows layout rules: horizontal segment first (left→right

    signal flow), unless hints request vertical-first routing.

    """

    if start == end:
        return (start,)

    if start.x == end.x or start.y == end.y:
        return _dedupe_collinear([start, end])

    if _prefer_horizontal_first(hints):
        corner = Point2D(end.x, start.y)

    else:
        corner = Point2D(start.x, end.y)

    return _dedupe_collinear([start, corner, end])


def points_to_segments(points: tuple[Point2D, ...]) -> tuple[Segment, ...]:
    """Convert a polyline into axis-aligned segments."""

    if len(points) < 2:
        return ()

    return tuple(Segment(points[i], points[i + 1]) for i in range(len(points) - 1))


def merge_routing_hints(*hint_groups: tuple[str, ...]) -> tuple[str, ...]:
    """Merge hint tuples deterministically (sorted unique)."""

    merged = sorted({hint for group in hint_groups for hint in group})

    return tuple(merged)
