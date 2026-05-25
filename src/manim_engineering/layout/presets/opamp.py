"""Op-amp inverting / integrator column layout preset."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.components import Capacitor, Ground, InputDriver, OpAmp, Resistor
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.nets import net_id_for_pins
from manim_engineering.layout.orientation import pin_local_in_aabb
from manim_engineering.layout.types import (
    ComponentOrientation,
    LabelPlacementMode,
    Point2D,
    TextPlacementOverride,
)

INPUT_COL_X = -1.2
OP_X = 0.5
OP_Y = 0.0
GND_STUB_X = -2.0
FEEDBACK_Y = OP_Y + 1.2
# flip_y places in_n on top and in_p on bottom (textbook inverting topology).
OP_ORIENTATION = ComponentOrientation(flip_y=True)
SUMMATION_Y = OP_Y + 0.75
IN_P_Y = OP_Y + 0.25
GND_CHANNEL_Y = OP_Y + 0.05
GND_WEST_X = OP_X - 0.45


def _connection_id(pin_a_id: str, pin_b_id: str) -> str:
    return "conn-" + "--".join(sorted([pin_a_id, pin_b_id]))


@dataclass(frozen=True)
class OpampLayoutPreset:
    """Placement overrides plus net hub and connection waypoints for net-aware routing."""

    overrides: dict[str, Point2D]
    orientation_overrides: dict[str, ComponentOrientation]
    net_waypoints: dict[str, Point2D]
    connection_waypoints: dict[str, tuple[Point2D, ...]]
    text_overrides: dict[str, tuple[TextPlacementOverride, ...]] = field(default_factory=dict)
    label_mode_overrides: dict[str, LabelPlacementMode] = field(default_factory=dict)


def inverting_integrator_preset(
    op1: OpAmp,
    rin: Resistor,
    feedback: Resistor | Capacitor,
    in_drv: InputDriver,
    gnd: Ground,
) -> OpampLayoutPreset:
    """Column layout: summation bus left of opamp; feedback rail above; GND stub to +."""
    summation = Point2D(INPUT_COL_X, SUMMATION_Y)
    out_anchor_x, out_anchor_y = op1.anchor_points["out"]
    out_local = pin_local_in_aabb(
        out_anchor_x,
        out_anchor_y,
        op1.get_bounds(),
        OP_ORIENTATION,
    )
    out_x = OP_X + out_local.x

    fb_id = feedback.element_id
    rin_id = rin.element_id
    op_id = op1.element_id

    summation_pins = frozenset(
        {
            f"{rin_id}.b",
            f"{fb_id}.a",
            f"{op_id}.in_n",
        }
    )

    overrides = {
        op_id: Point2D(OP_X, OP_Y),
        rin_id: origin_for_pin_at(rin, "b", summation),
        in_drv.element_id: origin_for_pin_at(
            in_drv, "out", Point2D(GND_STUB_X - 0.5, SUMMATION_Y)
        ),
        gnd.element_id: origin_for_pin_at(gnd, "gnd", Point2D(GND_STUB_X, GND_CHANNEL_Y)),
        fb_id: origin_for_pin_at(feedback, "b", Point2D(out_x, FEEDBACK_Y)),
    }

    net_waypoints = {
        net_id_for_pins(summation_pins): summation,
    }

    gnd_conn = _connection_id(gnd.get_pin("gnd").id, op1.get_pin("in_p").id)
    connection_waypoints = {
        gnd_conn: (
            Point2D(GND_WEST_X, IN_P_Y),
            Point2D(GND_WEST_X, GND_CHANNEL_Y),
            Point2D(GND_STUB_X, GND_CHANNEL_Y),
        ),
    }

    return OpampLayoutPreset(
        overrides=overrides,
        orientation_overrides={op_id: OP_ORIENTATION},
        net_waypoints=net_waypoints,
        connection_waypoints=connection_waypoints,
    )
