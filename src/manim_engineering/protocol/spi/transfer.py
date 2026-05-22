"""SPI transfer result types."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.state import TimingEvent


@dataclass(frozen=True)
class SPIStep:
    """One deterministic micro-step in a byte transfer."""

    time: float
    fsm_state: SPIFsmState
    line_owner: dict[str, SPIBusOwner]
    records: tuple[PropagationRecord, ...]
    timing_events: tuple[TimingEvent, ...]


@dataclass(frozen=True)
class SPITransferResult:
    """Outcome of :meth:`SPIController.transfer_byte`."""

    tx_byte: int
    rx_byte: int
    steps: tuple[SPIStep, ...]
    timing_events: tuple[TimingEvent, ...]
    final_fsm_state: SPIFsmState
