"""Single-pin stimulus marker for routing external signals into a circuit.

``InputDriver`` plays the role of "an externally-driven net" in teaching
diagrams: its single ``out`` port (PinDirection.OUT) can fan out to multiple
gate-style IN ports (e.g. both gates of a CMOS inverter) without violating the
IN-to-IN connection guard. It carries no physics in Scope A; its visual symbol
is a small right-pointing wedge whose tip sits at the ``out`` anchor.

Lives alongside :class:`VCC`/:class:`Ground` in ``components/common`` because
all three are zero-internal-state reference markers. ``semantic_type = "io"``
distinguishes it from the power rails for later renderer/theme dispatch.
"""

from __future__ import annotations

from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.enums import PinDirection, SignalType

_INPUT_DRIVER_BOUNDS = Bounds(width=0.5, height=0.4)
_INPUT_DRIVER_ANCHORS: dict[str, AnchorPoint] = {
    "out": (1.0, 0.5),
    "center": (0.5, 0.5),
}


class InputDriver(CircuitElement):
    """Single-pin source whose ``out`` drives downstream IN ports.

    ``signal_type`` selects the port signal type (default ``SignalType.ANALOG``
    so it can drive analog/MOSFET gates; pass ``SignalType.DIGITAL`` for
    logic-only scenes).
    """

    semantic_type = "io"

    def __init__(
        self,
        element_id: str,
        *,
        label: str | None = None,
        signal_type: SignalType = SignalType.ANALOG,
    ) -> None:
        self._signal_type = signal_type
        super().__init__(element_id, label=label)

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(_INPUT_DRIVER_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return _INPUT_DRIVER_BOUNDS

    @property
    def signal_type(self) -> SignalType:
        """Signal type carried by the ``out`` port (chosen at construction)."""
        return self._signal_type

    def _register_pins(self) -> None:
        self._register_pin(
            "out",
            direction=PinDirection.OUT,
            signal_type=self._signal_type,
            routing_hints=("horizontal", "right"),
        )
