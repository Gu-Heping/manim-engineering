"""Layout data types (no Manim, no renderer geometry)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from manim_engineering.components.types import Bounds

# Documented occupancy target per 50-layout-routing.md (60–75% of nominal frame).

OCCUPANCY_TARGET_MIN = 0.60

OCCUPANCY_TARGET_MAX = 0.75


# Default nominal frame for layout smoke and analog-first fixtures. Height 0.60
# accommodates taller analog symbols versus the retired basics catalog.

DEFAULT_NOMINAL_FRAME = Bounds(width=2.5, height=0.60)

# Shortest routed segment for coincident pins (topology shared, visual stub required).
MIN_VISIBLE_STUB = 0.08


@dataclass(frozen=True)
class Point2D:
    """A point in abstract layout/world coordinates."""

    x: float

    y: float


_VALID_ROTATIONS = frozenset({0, 90, 180, 270})


@dataclass(frozen=True)
class ComponentOrientation:
    """Placement-time rotation / mirror (layout-owned; components stay canonical)."""

    rotation: int = 0
    flip_x: bool = False
    flip_y: bool = False

    def __post_init__(self) -> None:
        if self.rotation not in _VALID_ROTATIONS:
            msg = f"rotation must be one of {sorted(_VALID_ROTATIONS)}, got {self.rotation}"
            raise ValueError(msg)


@dataclass(frozen=True)
class Segment:
    """Orthogonal wire segment between two points."""

    start: Point2D

    end: Point2D


@dataclass(frozen=True)
class TextPlacementOverride:
    """Optional world position for a renderer text role on one placement."""

    role: str

    world: Point2D

    label: str | None = None


class LabelPlacementMode(Enum):
    """How upright ``component_label`` picks a screen slot when not overridden."""

    AUTO = "auto"
    SLOT_ONLY = "slot_only"


@dataclass(frozen=True)
class ComponentPlacement:
    """World-space origin (bottom-left of oriented AABB) for a placed component."""

    element_id: str

    origin: Point2D

    bounds: Bounds

    orientation: ComponentOrientation = ComponentOrientation()

    text_overrides: tuple[TextPlacementOverride, ...] = ()

    label_mode: LabelPlacementMode = LabelPlacementMode.AUTO


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

    junction_nodes: frozenset[Point2D] = frozenset()
