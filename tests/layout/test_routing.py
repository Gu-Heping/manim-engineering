"""Routing unit tests — sibling-pin avoidance and bend order."""

from __future__ import annotations

from manim_engineering.layout.routing import route_orthogonal, points_to_segments, route_through_waypoints, segments_intersect
from manim_engineering.layout.types import Point2D, Segment


def test_route_flips_when_vertical_segment_passes_sibling_pin() -> None:
    """GND→in_p must not drop through in_n on the same x column."""
    in_p = Point2D(0.0, 0.75)
    gnd = Point2D(-1.6, -0.2)
    in_n = Point2D(0.0, 0.25)
    hints = ("down", "horizontal", "vertical")

    points = route_orthogonal(in_p, gnd, hints=hints, avoid_points=(in_n,))

    assert points[0] == in_p
    assert points[-1] == gnd
    assert not any(
        pt.x == in_n.x and min(in_p.y, gnd.y) < pt.y < max(in_p.y, gnd.y) and pt != in_p
        for pt in points
    )
    # Horizontal-first detour: corner at (-1.6, 0.75)
    assert any(pt.y == in_p.y and pt.x < 0 for pt in points)


def test_route_keeps_vertical_first_without_sibling_conflict() -> None:
    start = Point2D(1.0, 0.5)
    end = Point2D(2.0, 2.0)
    hints = ("down", "horizontal", "up", "vertical")

    points = route_orthogonal(start, end, hints=hints, avoid_points=())

    assert points == (start, Point2D(1.0, 2.0), end)


def test_route_through_waypoints_detours_below_bus() -> None:
    start = Point2D(0.5, 0.75)
    end = Point2D(-2.0, 0.75)
    waypoints = (Point2D(0.5, 0.05), Point2D(-2.0, 0.05))

    points = route_through_waypoints(start, end, waypoints)

    assert points[0] == start
    assert points[-1] == end
    assert any(pt.y == 0.05 for pt in points)
    assert not any(
        pt.x == -1.2 and 0.25 < pt.y < 0.75 for pt in points if pt.y != 0.75
    )


def test_points_to_segments_skips_zero_length_legs() -> None:
    points = (Point2D(1.0, 1.0), Point2D(1.0, 1.0), Point2D(1.0, 0.5))
    segments = points_to_segments(points)
    assert len(segments) == 1
    assert segments[0].start == Point2D(1.0, 1.0)
    assert segments[0].end == Point2D(1.0, 0.5)


def test_segments_intersect_detects_bus_crossing() -> None:
    gnd = Segment(Point2D(-2.0, 0.75), Point2D(0.5, 0.75))
    bus = Segment(Point2D(-1.2, 0.25), Point2D(-1.2, 1.2))
    assert segments_intersect(gnd, bus)
