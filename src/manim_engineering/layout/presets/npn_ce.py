"""Common-emitter NPN vertical stack preset (spine bus + resistor stubs)."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.components import NPN, VCC, Ground, InputDriver, Resistor
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.types import (
    ComponentOrientation,
    LabelPlacementMode,
    Point2D,
    TextPlacementOverride,
)

SPINE_X = 0.0
COLLECTOR_Y = 1.4
EMITTER_Y = 0.6
GND_Y = 0.0
RC_STUB_X = SPINE_X - 0.3
RE_STUB_X = SPINE_X + 0.3
VCC_RAIL_GAP = 0.55
VCC_X = RC_STUB_X - 1.0 - VCC_RAIL_GAP
RE_END_X = RE_STUB_X + 1.0
BASE_INPUT_X = SPINE_X - 1.5


@dataclass(frozen=True)
class NpnCeLayoutPreset:
    """Placement overrides for a spine-aligned CE amplifier."""

    overrides: dict[str, Point2D]
    orientation_overrides: dict[str, ComponentOrientation] = field(default_factory=dict)
    text_overrides: dict[str, tuple[TextPlacementOverride, ...]] = field(default_factory=dict)
    label_mode_overrides: dict[str, LabelPlacementMode] = field(default_factory=dict)


def common_emitter_preset(
    vcc: VCC,
    gnd: Ground,
    rc: Resistor,
    re: Resistor,
    q1: NPN,
    in_drv: InputDriver,
) -> NpnCeLayoutPreset:
    """VCC→Rc→Q1→Re→GND on a spine with resistors offset from the bus."""
    emitter = Point2D(SPINE_X, EMITTER_Y)

    overrides = {
        q1.element_id: origin_for_pin_at(q1, "emitter", emitter),
        rc.element_id: origin_for_pin_at(rc, "b", Point2D(RC_STUB_X, COLLECTOR_Y)),
        re.element_id: origin_for_pin_at(re, "a", Point2D(RE_STUB_X, EMITTER_Y)),
        vcc.element_id: origin_for_pin_at(vcc, "vcc", Point2D(VCC_X, COLLECTOR_Y)),
        gnd.element_id: origin_for_pin_at(gnd, "gnd", Point2D(RE_END_X, GND_Y)),
        in_drv.element_id: origin_for_pin_at(
            in_drv,
            "out",
            Point2D(BASE_INPUT_X, emitter.y + 0.4),
        ),
    }
    return NpnCeLayoutPreset(overrides=overrides)
