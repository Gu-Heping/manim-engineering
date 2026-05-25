"""P-channel enhancement MOSFET (four-terminal textbook-vertical footprint)."""

from __future__ import annotations

from typing import ClassVar

from manim_engineering.components.analog.mosfet import (
    ChannelPolarity,
    ConductionMode,
    MOSFET_BOUNDS,
    PMOS_ANCHORS,
    register_mosfet_pins,
)
from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds


class PMOS(CircuitElement):
    """P-channel enhancement MOSFET. Channel conducts when ``gate`` is LOW."""

    semantic_type = "analog"
    conduction_mode: ClassVar[ConductionMode] = "enhancement"
    channel_polarity: ClassVar[ChannelPolarity] = "p"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(PMOS_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return MOSFET_BOUNDS

    def _register_pins(self) -> None:
        register_mosfet_pins(self, p_channel=True)
