"""Measurement probe components."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_VOLTAGE_PROBE_BOUNDS = Bounds(width=0.9, height=0.9)
_VOLTAGE_PROBE_ANCHORS: dict[str, AnchorPoint] = {
    "pos": (0.0, 0.68),
    "neg": (0.0, 0.32),
    "center": (0.5, 0.5),
}

_CURRENT_PROBE_BOUNDS = Bounds(width=0.9, height=0.7)
_CURRENT_PROBE_ANCHORS: dict[str, AnchorPoint] = {
    "in": (0.0, 0.5),
    "out": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class VoltageProbe(CircuitElement):
    """High-impedance differential voltage probe."""

    semantic_type = "measurement"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_VOLTAGE_PROBE_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _VOLTAGE_PROBE_BOUNDS

    @property
    def port_pos(self):
        """Positive sense port."""
        return self.get_port("pos")

    @property
    def port_neg(self):
        """Negative sense port."""
        return self.get_port("neg")

    def _register_pins(self) -> None:
        for name in ("pos", "neg"):
            self._register_pin(
                name,
                direction=PinDirection.IN,
                signal_type=SignalType.ANALOG,
                routing_hints=("horizontal",),
            )


class CurrentProbe(CircuitElement):
    """Inline current probe with pass-through terminals."""

    semantic_type = "measurement"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_CURRENT_PROBE_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _CURRENT_PROBE_BOUNDS

    @property
    def port_in(self):
        """Input-side current terminal."""
        return self.get_port("in")

    @property
    def port_out(self):
        """Output-side current terminal."""
        return self.get_port("out")

    def _register_pins(self) -> None:
        for name in ("in", "out"):
            self._register_pin(
                name,
                direction=PinDirection.INOUT,
                signal_type=SignalType.ANALOG,
                routing_hints=("horizontal",),
            )
