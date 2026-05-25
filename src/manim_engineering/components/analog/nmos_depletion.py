"""N-channel depletion MOSFET (four-terminal textbook-vertical footprint)."""

from __future__ import annotations

from typing import ClassVar

from manim_engineering.components.analog.mosfet import (
    ChannelPolarity,
    ConductionMode,
    MOSFET_BOUNDS,
    NMOS_ANCHORS,
    register_mosfet_pins,
)
from manim_engineering.components.element import AnchorPoint, CircuitElement
from manim_engineering.components.types import Bounds


class NMOSDepletion(CircuitElement):
    """N-channel depletion MOSFET. Default-on channel; gate can pinch off."""

    semantic_type = "analog"
    conduction_mode: ClassVar[ConductionMode] = "depletion"
    channel_polarity: ClassVar[ChannelPolarity] = "n"

    @property
    def anchor_points(self) -> dict[str, AnchorPoint]:
        return dict(NMOS_ANCHORS)

    @property
    def bounds(self) -> Bounds:
        return MOSFET_BOUNDS

    def _register_pins(self) -> None:
        register_mosfet_pins(self, p_channel=False)
