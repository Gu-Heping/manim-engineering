"""Two-terminal resistor component stub."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.semantic.enums import PinDirection, SignalType

_RESISTOR_BOUNDS = Bounds(width=1.0, height=0.25)
_RESISTOR_ANCHORS: dict[str, AnchorPoint] = {
    "a": (0.0, 0.5),
    "b": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class Resistor(CircuitElement):
    """Passive resistor with symmetric terminals ``a`` and ``b``."""

    semantic_type = "passive"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_RESISTOR_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _RESISTOR_BOUNDS

    @property
    def port_a(self):
        """Left terminal port ``a``."""
        return self.get_port("a")

    @property
    def port_b(self):
        """Right terminal port ``b``."""
        return self.get_port("b")

    def _register_pins(self) -> None:
        for name in ("a", "b"):
            self._register_pin(
                name,
                direction=PinDirection.INOUT,
                signal_type=SignalType.SIGNAL,
                routing_hints=("horizontal",),
            )
