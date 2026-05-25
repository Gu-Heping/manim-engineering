"""Upright text placement after component orientation transforms."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from manim import Mobject, VGroup

from manim_engineering.components.analog import (
    NMOS,
    NPN,
    PMOS,
    PNP,
    Diode,
    NMOSDepletion,
    OpAmp,
    PMOSDepletion,
    ZenerDiode,
)
from manim_engineering.components.common import VCC, Ground, InputDriver
from manim_engineering.components.element import CircuitElement
from manim_engineering.components.passive import Capacitor, Inductor, Resistor
from manim_engineering.components.types import Bounds
from manim_engineering.layout.aabb import aabb_overlap, segment_bbox
from manim_engineering.layout.engine import pin_world_position
from manim_engineering.layout.orientation import oriented_footprint, transform_local_point
from manim_engineering.layout.types import (
    ComponentPlacement,
    LabelPlacementMode,
    LayoutBBox,
    LayoutResult,
    Point2D,
    TextPlacementOverride,
)
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.labels import LABEL_Z_INDEX, iter_label_roots, label_role

_MOS_TYPES = (NMOS, NMOSDepletion, PMOS, PMOSDepletion)
_VERTICAL_LABEL_TYPES = (Resistor, Capacitor, Inductor, Diode, ZenerDiode)
_PIN_LABEL_OUTSIDE_MARGIN = 0.30
_OPAMP_GLYPH_OFFSET_X = 0.32
_VERTICAL_FOOTPRINT_RATIO = 1.05
_LABEL_BAND_EPS = 0.02


class TextRelativeSlot(Enum):
    """Screen-fixed anchor relative to an oriented footprint AABB."""

    BELOW_CENTER = "below_center"
    ABOVE_CENTER = "above_center"
    LEFT_MID = "left_mid"
    RIGHT_MID = "right_mid"
    CENTER = "center"
    PIN_SCREEN_OFFSET = "pin_screen_offset"
    INTERFACE_PIN = "interface_pin"


@dataclass(frozen=True)
class DetachedLabel:
    """A label removed from a component mob before geometry orientation."""

    mob: Mobject
    local: Point2D
    role: str


def _remove_from_tree(root: Mobject, target: Mobject) -> None:
    """Remove ``target`` from the first ancestor that lists it as a submobject."""
    if target in root.submobjects:
        root.remove(target)
        return
    for sub in root.submobjects:
        _remove_from_tree(sub, target)


def detach_label_roots(mob: Mobject) -> tuple[Mobject, tuple[DetachedLabel, ...]]:
    """Remove ``label_text`` roots from ``mob`` and record local anchor positions."""
    detached: list[DetachedLabel] = []
    for label in iter_label_roots(mob):
        center = label.get_center()
        local = Point2D(float(center[0]), float(center[1]))
        role = label_role(label) or ""
        detached.append(DetachedLabel(label, local, role))
        _remove_from_tree(mob, label)
    return mob, tuple(detached)


def local_point_world(
    local: Point2D,
    placement: ComponentPlacement,
    nominal: Bounds,
) -> Point2D:
    """Map a component-local point to world space using placement orientation."""
    transformed = transform_local_point(local.x, local.y, nominal, placement.orientation)
    _bounds, offset = oriented_footprint(nominal, placement.orientation)
    return Point2D(
        placement.origin.x + transformed.x - offset.x,
        placement.origin.y + transformed.y - offset.y,
    )


def footprint_world_rect(placement: ComponentPlacement) -> tuple[float, float, float, float]:
    """Return oriented footprint AABB in world space as ``(min_x, min_y, max_x, max_y)``."""
    min_x = placement.origin.x
    min_y = placement.origin.y
    max_x = min_x + placement.bounds.width
    max_y = min_y + placement.bounds.height
    return min_x, min_y, max_x, max_y


def _placement_bbox(placement: ComponentPlacement) -> LayoutBBox:
    min_x, min_y, max_x, max_y = footprint_world_rect(placement)
    return LayoutBBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)


def is_vertical_footprint(placement: ComponentPlacement) -> bool:
    """True when the oriented AABB is taller than it is wide."""
    return placement.bounds.height > placement.bounds.width * _VERTICAL_FOOTPRINT_RATIO


def is_vertical_label_element(element: CircuitElement) -> bool:
    """Two-terminal passives/diodes eligible for vertical auto side-picking."""
    return isinstance(element, _VERTICAL_LABEL_TYPES)


def _label_band_width(nominal: Bounds) -> float:
    return theme.MOSFET_LABEL_LEFT_OFFSET * nominal.width + theme.COMPONENT_LABEL_Y_OFFSET


def _label_band(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    side: TextRelativeSlot,
    band_width: float,
) -> LayoutBBox:
    if side is TextRelativeSlot.LEFT_MID:
        return LayoutBBox(
            min_x=min_x - band_width,
            min_y=min_y,
            max_x=min_x - _LABEL_BAND_EPS,
            max_y=max_y,
        )
    return LayoutBBox(
        min_x=max_x + _LABEL_BAND_EPS,
        min_y=min_y,
        max_x=max_x + band_width,
        max_y=max_y,
    )


def _band_collision_score(
    band: LayoutBBox,
    placement: ComponentPlacement,
    layout: LayoutResult,
) -> float:
    score = 0.0
    for other in layout.placements:
        if other.element_id == placement.element_id:
            continue
        if aabb_overlap(band, _placement_bbox(other)):
            score += 1.0
    for wire in layout.wires:
        for segment in wire.segments:
            if aabb_overlap(band, segment_bbox(segment)):
                score += 0.5
    return score


def _horizontal_clearance(
    band: LayoutBBox,
    placement: ComponentPlacement,
    layout: LayoutResult,
) -> float:
    """Distance from band outer edge to nearest foreign footprint on the same side."""
    self_box = _placement_bbox(placement)
    if band.max_x <= self_box.min_x + _LABEL_BAND_EPS:
        gaps = [
            self_box.min_x - _placement_bbox(other).max_x
            for other in layout.placements
            if _placement_bbox(other).max_x <= self_box.min_x
        ]
    else:
        gaps = [
            _placement_bbox(other).min_x - self_box.max_x
            for other in layout.placements
            if _placement_bbox(other).min_x >= self_box.max_x
        ]
    return max(gaps, default=1e6)


def pick_vertical_label_side(
    placement: ComponentPlacement,
    element: CircuitElement,
    layout: LayoutResult,
) -> TextRelativeSlot:
    """Pick LEFT or RIGHT label band with the lowest collision score."""
    nominal = element.get_bounds()
    min_x, min_y, max_x, max_y = footprint_world_rect(placement)
    band_width = _label_band_width(nominal)
    left_band = _label_band(min_x, min_y, max_x, max_y, TextRelativeSlot.LEFT_MID, band_width)
    right_band = _label_band(min_x, min_y, max_x, max_y, TextRelativeSlot.RIGHT_MID, band_width)
    left_score = _band_collision_score(left_band, placement, layout)
    right_score = _band_collision_score(right_band, placement, layout)
    if left_score < right_score:
        return TextRelativeSlot.LEFT_MID
    if right_score < left_score:
        return TextRelativeSlot.RIGHT_MID
    left_gap = _horizontal_clearance(left_band, placement, layout)
    right_gap = _horizontal_clearance(right_band, placement, layout)
    if right_gap > left_gap:
        return TextRelativeSlot.RIGHT_MID
    return TextRelativeSlot.LEFT_MID


def slot_for_role(role: str, element: CircuitElement) -> TextRelativeSlot | None:
    """Map a renderer text role to a screen-fixed placement slot."""
    if role == "component_label":
        if isinstance(element, Ground):
            return TextRelativeSlot.BELOW_CENTER
        if isinstance(element, VCC):
            return TextRelativeSlot.ABOVE_CENTER
        if isinstance(element, _MOS_TYPES):
            return TextRelativeSlot.LEFT_MID
        if isinstance(element, (NPN, PNP, OpAmp, ZenerDiode, Diode)):
            return TextRelativeSlot.BELOW_CENTER
        if isinstance(element, InputDriver):
            return TextRelativeSlot.ABOVE_CENTER
        if getattr(element, "semantic_type", "") == "interface":
            return TextRelativeSlot.ABOVE_CENTER
        return TextRelativeSlot.ABOVE_CENTER
    if role in ("opamp.plus", "opamp.minus"):
        return TextRelativeSlot.PIN_SCREEN_OFFSET
    if role == "interface.role":
        return TextRelativeSlot.CENTER
    if role.startswith("interface.pin."):
        return TextRelativeSlot.INTERFACE_PIN
    return None


def _resolve_component_label_slot(
    placement: ComponentPlacement,
    element: CircuitElement,
    layout: LayoutResult | None,
) -> TextRelativeSlot | None:
    if (
        placement.label_mode is LabelPlacementMode.AUTO
        and is_vertical_footprint(placement)
        and is_vertical_label_element(element)
    ):
        if layout is not None:
            return pick_vertical_label_side(placement, element, layout)
        return TextRelativeSlot.LEFT_MID
    return slot_for_role("component_label", element)


def _component_label_font_fudge() -> float:
    return theme.COMPONENT_LABEL_FONT_SIZE * 0.02


def _interface_pin_world(
    role: str,
    placement: ComponentPlacement,
    element: CircuitElement,
    *,
    local_fallback: Point2D,
) -> Point2D:
    pin_name = role.removeprefix("interface.pin.")
    anchors = element.anchor_points
    if pin_name not in anchors:
        return local_fallback
    pin_world = pin_world_position(placement, element, pin_name)
    ax, ay = anchors[pin_name]
    min_x, min_y, max_x, max_y = footprint_world_rect(placement)
    margin = _PIN_LABEL_OUTSIDE_MARGIN
    if ax <= 0.05:
        return Point2D(min_x - margin, pin_world.y)
    if ax >= 0.95:
        return Point2D(max_x + margin, pin_world.y)
    if ay <= 0.05:
        return Point2D(pin_world.x, min_y - margin)
    if ay >= 0.95:
        return Point2D(pin_world.x, max_y + margin)
    return Point2D(pin_world.x, max_y + margin)


def _world_for_slot(
    slot: TextRelativeSlot,
    placement: ComponentPlacement,
    nominal: Bounds,
    element: CircuitElement,
    role: str,
    *,
    local_fallback: Point2D,
) -> Point2D:
    min_x, min_y, max_x, max_y = footprint_world_rect(placement)
    max_x - min_x
    height = max_y - min_y
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    font_fudge = _component_label_font_fudge()

    if slot is TextRelativeSlot.CENTER:
        return Point2D(center_x, center_y)

    if slot is TextRelativeSlot.LEFT_MID:
        return Point2D(
            min_x - theme.MOSFET_LABEL_LEFT_OFFSET * nominal.width,
            center_y,
        )

    if slot is TextRelativeSlot.RIGHT_MID:
        return Point2D(
            max_x + theme.MOSFET_LABEL_LEFT_OFFSET * nominal.width,
            center_y,
        )

    if slot is TextRelativeSlot.BELOW_CENTER:
        if isinstance(element, Ground):
            offset = theme.POWER_LABEL_BELOW_OFFSET
        else:
            offset = theme.COMPONENT_LABEL_Y_OFFSET * height + font_fudge
        return Point2D(center_x, min_y - offset)

    if slot is TextRelativeSlot.ABOVE_CENTER:
        if isinstance(element, VCC):
            offset = theme.POWER_LABEL_ABOVE_OFFSET
        elif isinstance(element, InputDriver):
            offset = 0.18
        else:
            offset = theme.COMPONENT_LABEL_Y_OFFSET * height + font_fudge
        return Point2D(center_x, max_y + offset)

    if slot is TextRelativeSlot.PIN_SCREEN_OFFSET:
        pin_name = "in_p" if role == "opamp.plus" else "in_n"
        pin = pin_world_position(placement, element, pin_name)
        return Point2D(pin.x + _OPAMP_GLYPH_OFFSET_X * nominal.width, pin.y)

    if slot is TextRelativeSlot.INTERFACE_PIN:
        return _interface_pin_world(role, placement, element, local_fallback=local_fallback)

    return local_fallback


def world_position_for_label(
    role: str,
    placement: ComponentPlacement,
    nominal: Bounds,
    element: CircuitElement,
    *,
    local_fallback: Point2D,
    layout: LayoutResult | None = None,
) -> Point2D:
    """Resolve a detached label role to a screen-fixed world position."""
    if role == "component_label":
        slot = _resolve_component_label_slot(placement, element, layout)
    else:
        slot = slot_for_role(role, element)
    if slot is None:
        if (
            role == "component_label"
            and placement.label_mode is LabelPlacementMode.AUTO
            and is_vertical_footprint(placement)
            and is_vertical_label_element(element)
        ):
            slot = TextRelativeSlot.LEFT_MID
        else:
            return local_fallback
    return _world_for_slot(
        slot,
        placement,
        nominal,
        element,
        role,
        local_fallback=local_fallback,
    )


def _override_map(
    overrides: tuple[TextPlacementOverride, ...],
) -> dict[str, Point2D]:
    return {item.role: item.world for item in overrides}


def place_labels_upright(
    labels: tuple[DetachedLabel, ...],
    placement: ComponentPlacement,
    nominal: Bounds,
    element: CircuitElement,
    *,
    layout: LayoutResult | None = None,
) -> tuple[Mobject, ...]:
    """Reposition detached labels in world space without flip/rotate on glyphs."""
    overrides = _override_map(placement.text_overrides)
    placed: list[Mobject] = []
    for item in labels:
        if item.role in overrides:
            world = overrides[item.role]
        else:
            fallback = local_point_world(item.local, placement, nominal)
            world = world_position_for_label(
                item.role,
                placement,
                nominal,
                element,
                local_fallback=fallback,
                layout=layout,
            )
        item.mob.move_to(np.array([world.x, world.y, 0.0]))
        item.mob.set_z_index(LABEL_Z_INDEX)
        placed.append(item.mob)
    return tuple(placed)


def place_component_mob(
    mob: Mobject,
    placement: ComponentPlacement,
    nominal: Bounds,
    element: CircuitElement,
    *,
    place_geometry,
    layout: LayoutResult | None = None,
) -> VGroup:
    """Orient stroke geometry, then attach upright labels."""
    geometry, labels = detach_label_roots(mob)
    oriented = place_geometry(geometry, placement)
    upright = place_labels_upright(labels, placement, nominal, element, layout=layout)
    if upright:
        return VGroup(oriented, *upright)
    return VGroup(oriented)
