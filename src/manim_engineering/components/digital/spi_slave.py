"""SPI slave interface stub for layout and protocol examples."""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_SPI_BOUNDS = Bounds(width=1.4, height=1.0)
_SPI_ANCHORS: dict[str, AnchorPoint] = {
    "clk": (1.0, 0.85),
    "mosi": (1.0, 0.5),
    "miso": (0.0, 0.5),
    "cs": (1.0, 0.15),
    "center": (0.5, 0.5),
}


class SPISlave(CircuitElement):
    """SPI slave: receives clk, mosi, cs; drives miso."""

    semantic_type = "interface"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_SPI_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _SPI_BOUNDS

    def _register_pins(self) -> None:
        self._register_pin("clk", direction=PinDirection.IN, signal_type=SignalType.CLOCK)
        self._register_pin("mosi", direction=PinDirection.IN, signal_type=SignalType.DATA)
        self._register_pin("miso", direction=PinDirection.OUT, signal_type=SignalType.DATA)
        self._register_pin(
            "cs",
            direction=PinDirection.IN,
            signal_type=SignalType.DIGITAL,
            routing_hints=("horizontal",),
        )
