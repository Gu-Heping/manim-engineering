"""UART port stub for layout and protocol examples."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.semantic.enums import PinDirection, SignalType

_UART_BOUNDS = Bounds(width=1.0, height=0.7)
_UART_ANCHORS: dict[str, AnchorPoint] = {
    "tx": (0.0, 0.65),
    "rx": (0.0, 0.35),
    "gnd": (0.5, 0.0),
    "center": (0.5, 0.5),
}


class UARTPort(CircuitElement):
    """UART interface: TX out, RX in, GND reference (layout only for gnd)."""

    semantic_type = "interface"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_UART_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _UART_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin("tx", direction=PinDirection.OUT, signal_type=SignalType.DATA)
        self._register_pin("rx", direction=PinDirection.IN, signal_type=SignalType.DATA)
        self._register_pin(
            "gnd",
            direction=PinDirection.IN,
            signal_type=SignalType.GROUND,
            routing_hints=("vertical",),
        )
