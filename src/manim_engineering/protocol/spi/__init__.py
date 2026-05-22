"""SPI protocol semantics: FSM, ownership, timing, byte transfer."""

from manim_engineering.protocol.spi.binding import SPIBusBinding
from manim_engineering.protocol.spi.controller import SPIController
from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState, SPIMode, SPIRole
from manim_engineering.protocol.spi.transfer import SPIStep, SPITransferResult

__all__ = [
    "SPIBusBinding",
    "SPIBusOwner",
    "SPIController",
    "SPIFsmState",
    "SPIMode",
    "SPIRole",
    "SPIStep",
    "SPITransferResult",
]
