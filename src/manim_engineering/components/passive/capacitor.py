"""Two-terminal capacitor component stub."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.semantic.enums import PinDirection, SignalType

_CAPACITOR_BOUNDS = Bounds(width=0.6, height=0.5)
_CAPACITOR_ANCHORS: dict[str, AnchorPoint] = {
    "a": (0.0, 0.5),
    "b": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class Capacitor(CircuitElement):
    """Passive capacitor with symmetric terminals ``a`` and ``b``."""

    semantic_type = "passive"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_CAPACITOR_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _CAPACITOR_BOUNDS

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
