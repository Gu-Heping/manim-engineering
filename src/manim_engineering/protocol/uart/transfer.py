"""UART transfer result types."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.protocol.uart.enums import UARTFsmState, UARTLineOwner
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.state import TimingEvent


@dataclass(frozen=True)
class UARTStep:
    """One deterministic micro-step in a byte transmission."""

    time: float
    fsm_state: UARTFsmState
    line_owner: dict[str, UARTLineOwner]
    records: tuple[PropagationRecord, ...]
    timing_events: tuple[TimingEvent, ...]


@dataclass(frozen=True)
class UARTTransferResult:
    """Outcome of :meth:`UARTController.transmit_byte`."""

    tx_byte: int
    steps: tuple[UARTStep, ...]
    timing_events: tuple[TimingEvent, ...]
    final_fsm_state: UARTFsmState
    bit_period: float
