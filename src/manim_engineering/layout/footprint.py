"""Wire vs component footprint checks (layout world coordinates)."""

from __future__ import annotations

from manim_engineering.layout.types import ComponentPlacement, LayoutResult, Point2D, Segment

_INTERIOR_EPS = 1e-4


def _footprint_interior(placement: ComponentPlacement) -> tuple[float, float, float, float]:
    """Axis-aligned interior (exclusive of outer edge) for overlap tests."""
    ox, oy = placement.origin.x, placement.origin.y
    w, h = placement.bounds.width, placement.bounds.height
    return (
        ox + _INTERIOR_EPS,
        oy + _INTERIOR_EPS,
        ox + w - _INTERIOR_EPS,
        oy + h - _INTERIOR_EPS,
    )


def _point_in_interior(x: float, y: float, placement: ComponentPlacement) -> bool:
    ix0, iy0, ix1, iy1 = _footprint_interior(placement)
    return ix0 < x < ix1 and iy0 < y < iy1


def segment_crosses_footprint_interior(
    segment: Segment,
    placement: ComponentPlacement,
) -> bool:
    """True when any point of the segment lies strictly inside the placement box."""
    if segment.start.x == segment.end.x:
        x = segment.start.x
        y0, y1 = sorted((segment.start.y, segment.end.y))
        ix0, iy0, ix1, iy1 = _footprint_interior(placement)
        if not (ix0 < x < ix1):
            return False
        y_mid = 0.5 * (y0 + y1)
        return iy0 < y_mid < iy1
    if segment.start.y == segment.end.y:
        y = segment.start.y
        x0, x1 = sorted((segment.start.x, segment.end.x))
        ix0, iy0, ix1, iy1 = _footprint_interior(placement)
        if not (iy0 < y < iy1):
            return False
        x_mid = 0.5 * (x0 + x1)
        return ix0 < x_mid < ix1
    return False


def wires_avoid_footprints(
    layout: LayoutResult,
    *,
    allowed_touch_ids: frozenset[str] | None = None,
) -> list[str]:
    """Return human-readable violations when a wire segment crosses a component interior.

    Endpoints on pin anchors may lie on the footprint border; only strict interior
    crossings are reported. Pass ``allowed_touch_ids`` to skip checks against
    specific elements (rare; default checks all placements).
    """
    skip = allowed_touch_ids or frozenset()
    violations: list[str] = []
    placements = [p for p in layout.placements if p.element_id not in skip]

    for wire in layout.wires:
        for segment in wire.segments:
            for placement in placements:
                if segment_crosses_footprint_interior(segment, placement):
                    violations.append(
                        f"{wire.connection_id}: segment "
                        f"({segment.start.x:.3f},{segment.start.y:.3f})→"
                        f"({segment.end.x:.3f},{segment.end.y:.3f}) "
                        f"crosses interior of {placement.element_id}"
                    )
    return violations


def assert_wires_avoid_footprints(layout: LayoutResult) -> None:
    """Raise AssertionError when any routed segment crosses a component interior."""
    violations = wires_avoid_footprints(layout)
    if violations:
        raise AssertionError("; ".join(violations))
