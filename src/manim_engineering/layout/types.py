"""Layout data types (no Manim, no renderer geometry)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.components.types import Bounds

# Documented occupancy target per 50-layout-routing.md (60–75% of nominal frame).

OCCUPANCY_TARGET_MIN = 0.60

OCCUPANCY_TARGET_MAX = 0.75


# Default nominal frame sized for the two-resistor basics fixture (~71% occupancy).

DEFAULT_NOMINAL_FRAME = Bounds(width=2.5, height=0.35)


@dataclass(frozen=True)
class Point2D:
    """A point in abstract layout/world coordinates."""

    x: float

    y: float


@dataclass(frozen=True)
class Segment:
    """Orthogonal wire segment between two points."""

    start: Point2D

    end: Point2D


@dataclass(frozen=True)
class ComponentPlacement:
    """World-space origin (bottom-left) for a placed component."""

    element_id: str

    origin: Point2D

    bounds: Bounds


@dataclass(frozen=True)
class WirePath:
    """Routed connection as polyline points and derived segments."""

    connection_id: str

    points: tuple[Point2D, ...]

    segments: tuple[Segment, ...]


@dataclass(frozen=True)
class LayoutBBox:
    """Axis-aligned bounding box in layout world coordinates."""

    min_x: float

    min_y: float

    max_x: float

    max_y: float

    @property
    def width(self) -> float:

        return self.max_x - self.min_x

    @property
    def height(self) -> float:

        return self.max_y - self.min_y

    @property
    def area(self) -> float:

        return self.width * self.height


@dataclass(frozen=True)
class LayoutResult:
    """Full layout output: placements, pin positions, routed wires, occupancy."""

    placements: tuple[ComponentPlacement, ...]

    pin_positions: dict[str, Point2D]

    wires: tuple[WirePath, ...]

    frame: Bounds

    occupancy_ratio: float

    layout_bbox: LayoutBBox

    scene_bbox: LayoutBBox
