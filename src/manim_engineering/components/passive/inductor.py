"""Two-terminal inductor component stub."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_INDUCTOR_BOUNDS = Bounds(width=1.0, height=0.40)
_INDUCTOR_ANCHORS: dict[str, AnchorPoint] = {
    "a": (0.0, 0.5),
    "b": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class Inductor(CircuitElement):
    """Passive inductor with symmetric terminals ``a`` and ``b``."""

    semantic_type = "passive"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_INDUCTOR_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _INDUCTOR_BOUNDS

    def _register_pins(self) -> None:
        for name in ("a", "b"):
            self._register_pin(
                name,
                direction=PinDirection.INOUT,
                signal_type=SignalType.SIGNAL,
                routing_hints=("horizontal",),
            )
