"""Common power/reference component tests."""

from __future__ import annotations

from manim_engineering.components import VCC, Ground
from manim_engineering.core import PinDirection, SignalType


def test_ground_pin_naming() -> None:
    gnd = Ground("gnd1")
    assert gnd.semantic_type == "power"
    assert set(gnd.pins) == {"gnd"}
    pin = gnd.get_pin("gnd")
    assert pin.signal_type == SignalType.GROUND
    assert pin.direction == PinDirection.IN


def test_vcc_pin_naming() -> None:
    vcc = VCC("vcc1")
    assert vcc.semantic_type == "power"
    assert set(vcc.pins) == {"vcc"}
    pin = vcc.get_pin("vcc")
    assert pin.signal_type == SignalType.POWER
    assert pin.direction == PinDirection.OUT


def test_vcc_anchor_at_bottom_for_vertical_stack() -> None:
    vcc = VCC("vcc1")
    assert vcc.anchor_points["vcc"] == (0.5, 0.0)


def test_ground_anchor_at_top_for_vertical_stack() -> None:
    gnd = Ground("gnd1")
    assert gnd.anchor_points["gnd"] == (0.5, 1.0)
