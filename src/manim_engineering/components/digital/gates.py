"""Basic digital logic gate components."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_BINARY_GATE_BOUNDS = Bounds(width=1.0, height=0.8)
_BINARY_GATE_ANCHORS: dict[str, AnchorPoint] = {
    "a": (0.0, 0.72),
    "b": (0.0, 0.28),
    "out": (1.0, 0.5),
    "center": (0.5, 0.5),
}

_NOT_GATE_BOUNDS = Bounds(width=0.9, height=0.7)
_NOT_GATE_ANCHORS: dict[str, AnchorPoint] = {
    "in": (0.0, 0.5),
    "out": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class _BinaryLogicGate(CircuitElement):
    """Shared two-input digital gate contract."""

    semantic_type = "digital_gate"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_BINARY_GATE_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _BINARY_GATE_BOUNDS

    @property
    def port_a(self):
        """Input port ``a``."""
        return self.get_port("a")

    @property
    def port_b(self):
        """Input port ``b``."""
        return self.get_port("b")

    @property
    def port_out(self):
        """Output port ``out``."""
        return self.get_port("out")

    def _register_pins(self) -> None:
        for name in ("a", "b"):
            self._register_pin(
                name,
                direction=PinDirection.IN,
                signal_type=SignalType.DIGITAL,
                routing_hints=("horizontal",),
            )
        self._register_pin(
            "out",
            direction=PinDirection.OUT,
            signal_type=SignalType.DIGITAL,
            routing_hints=("horizontal",),
        )


class ANDGate(_BinaryLogicGate):
    """Two-input AND gate."""


class ORGate(_BinaryLogicGate):
    """Two-input OR gate."""


class NOTGate(CircuitElement):
    """Single-input inverter with explicit output port."""

    semantic_type = "digital_gate"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_NOT_GATE_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _NOT_GATE_BOUNDS

    @property
    def port_in(self):
        """Input port ``in``."""
        return self.get_port("in")

    @property
    def port_out(self):
        """Output port ``out``."""
        return self.get_port("out")

    def _register_pins(self) -> None:
        self._register_pin(
            "in",
            direction=PinDirection.IN,
            signal_type=SignalType.DIGITAL,
            routing_hints=("horizontal",),
        )
        self._register_pin(
            "out",
            direction=PinDirection.OUT,
            signal_type=SignalType.DIGITAL,
            routing_hints=("horizontal",),
        )
