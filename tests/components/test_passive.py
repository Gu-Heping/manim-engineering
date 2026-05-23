"""Passive component stub tests."""

from __future__ import annotations

from manim_engineering.components import Capacitor
from manim_engineering.core import PinDirection, SignalType


def test_capacitor_pins_and_semantic_type() -> None:
    c = Capacitor("c1")
    assert c.semantic_type == "passive"
    assert set(c.pins) == {"a", "b"}
    assert c.get_pin("a").signal_type == SignalType.SIGNAL
    assert c.get_pin("b").direction == PinDirection.INOUT
    assert c.get_bounds().width > 0
