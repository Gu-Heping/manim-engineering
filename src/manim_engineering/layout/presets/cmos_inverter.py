"""CMOS inverter vertical stack preset (rail / output / rail nodes)."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.components import NMOS, PMOS, VCC, Ground, InputDriver
from manim_engineering.components.analog.mosfet import MOSFET_DRAIN_STUB_X, MOSFET_SOURCE_STUB_X
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.types import (
    ComponentOrientation,
    LabelPlacementMode,
    Point2D,
    TextPlacementOverride,
)

RAIL_X = 0.0
# Shared drain x when PMOS/NMOS sources align to the left rail (stub column gap).
OUT_X = RAIL_X + (MOSFET_DRAIN_STUB_X - MOSFET_SOURCE_STUB_X)

# Vertical spine (top → bottom): S (VCC) · D (shared OUT) · S (GND).
GND_Y = 0.5
VCC_Y = 2.5
PMOS_DRAIN_Y = VCC_Y - 1.0
NMOS_DRAIN_Y = GND_Y + 1.0
DRAIN_Y = PMOS_DRAIN_Y
OUT_LABEL = Point2D(0.8, DRAIN_Y)
OUT_STUB_X = OUT_LABEL.x - 0.12

GATE_BUS_X = RAIL_X - 1.0
GATE_BUS_Y = (VCC_Y + GND_Y) * 0.5
IN_DRV_OFFSET_X = 1.0


@dataclass(frozen=True)
class CmosInverterLayoutPreset:
    """Bottom-left origins for a canonical PMOS-over-NMOS stack."""

    overrides: dict[str, Point2D]
    orientation_overrides: dict[str, ComponentOrientation] = field(default_factory=dict)
    text_overrides: dict[str, tuple[TextPlacementOverride, ...]] = field(default_factory=dict)
    label_mode_overrides: dict[str, LabelPlacementMode] = field(default_factory=dict)
    connection_waypoints: dict[str, tuple[Point2D, ...]] = field(default_factory=dict)


def cmos_inverter_preset(
    vcc: VCC,
    gnd: Ground,
    pmos: PMOS,
    nmos: NMOS,
    in_drv: InputDriver,
) -> CmosInverterLayoutPreset:
    """Vertical CMOS stack with spine order S–D–D–S (sources on rail, drains at OUT_X)."""
    pm_source = Point2D(RAIL_X, VCC_Y)
    nm_source = Point2D(RAIL_X, GND_Y)
    gate_bus = Point2D(GATE_BUS_X, GATE_BUS_Y)
    overrides = {
        pmos.element_id: origin_for_pin_at(pmos, "source", pm_source),
        nmos.element_id: origin_for_pin_at(nmos, "source", nm_source),
        vcc.element_id: origin_for_pin_at(vcc, "vcc", pm_source),
        gnd.element_id: origin_for_pin_at(gnd, "gnd", nm_source),
        in_drv.element_id: origin_for_pin_at(
            in_drv, "out", Point2D(gate_bus.x - IN_DRV_OFFSET_X, gate_bus.y)
        ),
    }
    drain_ids = sorted([pmos.get_pin("drain").id, nmos.get_pin("drain").id])
    drain_conn_id = f"conn-{drain_ids[0]}--{drain_ids[1]}"
    return CmosInverterLayoutPreset(
        overrides=overrides,
        text_overrides={
            pmos.element_id: (
                TextPlacementOverride(role="net_label", world=OUT_LABEL, label="OUT"),
            ),
        },
        connection_waypoints={
            drain_conn_id: (Point2D(OUT_STUB_X, DRAIN_Y),),
        },
    )
