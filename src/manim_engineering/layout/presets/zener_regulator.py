"""Zener shunt regulator preset (series Rs, parallel RL branch)."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.components import VCC, Ground, Resistor, ZenerDiode
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.types import (
    ComponentOrientation,
    LabelPlacementMode,
    Point2D,
    TextPlacementOverride,
)

JUNCTION = Point2D(0.0, 2.0)
GND_Y = 0.0
DZ_CATHODE = Point2D(0.0, 1.0)
RL_BRANCH_X = 1.0
VCC_Y = 3.0
# Rs vertical above junction; Dz vertical shunt to GND.
RS_ORIENTATION = ComponentOrientation(rotation=90)
DZ_ORIENTATION = ComponentOrientation(rotation=270)


@dataclass(frozen=True)
class ZenerRegulatorLayoutPreset:
    """Bottom-left origins for VCC→Rs→junction with Dz drop and RL branch."""

    overrides: dict[str, Point2D]
    orientation_overrides: dict[str, ComponentOrientation]
    text_overrides: dict[str, tuple[TextPlacementOverride, ...]] = field(default_factory=dict)
    label_mode_overrides: dict[str, LabelPlacementMode] = field(default_factory=dict)


def zener_regulator_preset(
    vcc: VCC,
    gnd: Ground,
    rs: Resistor,
    zd: ZenerDiode,
    rl: Resistor,
) -> ZenerRegulatorLayoutPreset:
    """VCC→Rs→junction; Dz drops from junction; RL branch to the right."""
    overrides = {
        rs.element_id: origin_for_pin_at(
            rs, "b", JUNCTION, orientation=RS_ORIENTATION
        ),
        vcc.element_id: origin_for_pin_at(
            vcc, "vcc", Point2D(JUNCTION.x, VCC_Y)
        ),
        zd.element_id: origin_for_pin_at(
            zd, "cathode", DZ_CATHODE, orientation=DZ_ORIENTATION
        ),
        rl.element_id: origin_for_pin_at(rl, "a", Point2D(RL_BRANCH_X, JUNCTION.y)),
        gnd.element_id: origin_for_pin_at(gnd, "gnd", Point2D(0.0, GND_Y)),
    }
    orientation_overrides = {
        rs.element_id: RS_ORIENTATION,
        zd.element_id: DZ_ORIENTATION,
    }
    return ZenerRegulatorLayoutPreset(
        overrides=overrides,
        orientation_overrides=orientation_overrides,
    )
