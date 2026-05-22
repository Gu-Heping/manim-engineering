"""Axis-aligned bounding box helpers for layout geometry guards (no Manim)."""

from __future__ import annotations

from manim_engineering.layout.types import LayoutBBox, Segment

AABB_EPS = 1e-9


def segment_bbox(segment: Segment) -> LayoutBBox:
    """Tight AABB for an orthogonal wire or waveform segment."""
    return LayoutBBox(
        min_x=min(segment.start.x, segment.end.x),
        min_y=min(segment.start.y, segment.end.y),
        max_x=max(segment.start.x, segment.end.x),
        max_y=max(segment.start.y, segment.end.y),
    )


def union_bbox(boxes: tuple[LayoutBBox, ...]) -> LayoutBBox | None:
    """Union of zero or more boxes; ``None`` when ``boxes`` is empty."""
    if not boxes:
        return None
    return LayoutBBox(
        min_x=min(box.min_x for box in boxes),
        min_y=min(box.min_y for box in boxes),
        max_x=max(box.max_x for box in boxes),
        max_y=max(box.max_y for box in boxes),
    )


def aabb_overlap(a: LayoutBBox, b: LayoutBBox, *, eps: float = AABB_EPS) -> bool:
    """True when closed AABBs share area (touching edges are not overlap)."""
    return not (
        a.max_x <= b.min_x + eps
        or b.max_x <= a.min_x + eps
        or a.max_y <= b.min_y + eps
        or b.max_y <= a.min_y + eps
    )


def vertical_gap_above(lower: LayoutBBox, upper: LayoutBBox) -> float:
    """
    Vertical separation when ``upper`` sits above ``lower`` (Y-up).

    Returns ``upper.min_y - lower.max_y`` when separated; ``0`` when bands overlap in Y.
    """
    if upper.min_y >= lower.max_y:
        return upper.min_y - lower.max_y
    return 0.0
