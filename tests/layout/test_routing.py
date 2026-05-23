"""Orthogonal routing tests (pin positions, not geometry overlap)."""

from __future__ import annotations

from manim_engineering.layout import Point2D, route_orthogonal


def test_route_orthogonal_horizontal_first_by_hint() -> None:

    start = Point2D(0.0, 0.5)

    end = Point2D(2.0, 1.0)

    points = route_orthogonal(start, end, hints=("horizontal",))

    assert points[0] == start

    assert points[-1] == end

    assert points[1] == Point2D(2.0, 0.5)


def test_route_orthogonal_vertical_first_by_hint() -> None:

    start = Point2D(0.0, 0.5)

    end = Point2D(2.0, 1.0)

    points = route_orthogonal(start, end, hints=("vertical",))

    assert points[1] == Point2D(0.0, 1.0)


def test_route_mixed_horizontal_vertical_prefers_vertical_first() -> None:
    """Resistor.b → NMOS.drain style hints must not bend at gate height."""
    start = Point2D(1.0, 0.5)
    end = Point2D(2.5, 1.0)
    points = route_orthogonal(
        start,
        end,
        hints=("down", "horizontal", "up", "vertical"),
    )
    assert points[1] == Point2D(1.0, 1.0)


def test_route_collinear_is_direct() -> None:

    start = Point2D(1.0, 0.0)

    end = Point2D(3.0, 0.0)

    assert route_orthogonal(start, end) == (start, end)
