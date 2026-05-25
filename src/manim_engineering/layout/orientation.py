"""Discrete component orientation transforms for layout and rendering."""

from __future__ import annotations

import math

from manim_engineering.components.types import Bounds
from manim_engineering.layout.types import ComponentOrientation, Point2D


def _rotate_cw(cx: float, cy: float, degrees: int) -> tuple[float, float]:
    if degrees == 0:
        return cx, cy
    radians = math.radians(degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return cx * cosine + cy * sine, -cx * sine + cy * cosine


def transform_local_point(
    x: float,
    y: float,
    nominal: Bounds,
    orientation: ComponentOrientation,
) -> Point2D:
    """Map a point in nominal local space through flip + clockwise rotation."""
    w, h = nominal.width, nominal.height
    cx, cy = x - w / 2, y - h / 2
    if orientation.flip_x:
        cx = -cx
    if orientation.flip_y:
        cy = -cy
    cx, cy = _rotate_cw(cx, cy, orientation.rotation)
    return Point2D(cx + w / 2, cy + h / 2)


def oriented_footprint(
    nominal: Bounds,
    orientation: ComponentOrientation,
) -> tuple[Bounds, Point2D]:
    """Return axis-aligned bounds and offset after orientation in nominal space."""
    w, h = nominal.width, nominal.height
    corners = [
        transform_local_point(x, y, nominal, orientation)
        for x, y in ((0.0, 0.0), (w, 0.0), (w, h), (0.0, h))
    ]
    min_x = min(point.x for point in corners)
    min_y = min(point.y for point in corners)
    max_x = max(point.x for point in corners)
    max_y = max(point.y for point in corners)
    return Bounds(width=max_x - min_x, height=max_y - min_y), Point2D(min_x, min_y)


def pin_local_in_aabb(
    anchor_x: float,
    anchor_y: float,
    nominal: Bounds,
    orientation: ComponentOrientation,
) -> Point2D:
    """Pin position in the oriented footprint's local AABB (origin = bottom-left)."""
    raw_x = anchor_x * nominal.width
    raw_y = anchor_y * nominal.height
    transformed = transform_local_point(raw_x, raw_y, nominal, orientation)
    _bounds, offset = oriented_footprint(nominal, orientation)
    return Point2D(transformed.x - offset.x, transformed.y - offset.y)
