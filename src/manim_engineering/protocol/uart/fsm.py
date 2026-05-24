"""UART finite-state machine transitions."""

from __future__ import annotations

from typing import Final

from manim_engineering.protocol.uart.enums import UARTFsmState, UARTLineOwner

# Semantic line ownership while the frame is active (idle defers to NONE below).
_ACTIVE_LINE_OWNERS: Final[dict[str, UARTLineOwner]] = {
    "tx": UARTLineOwner.TRANSMITTER,
    "rx": UARTLineOwner.RECEIVER,
}


def _require_state(current: UARTFsmState, expected: UARTFsmState) -> None:
    if current is not expected:
        raise ValueError(f"expected {expected.value}, got {current.value}")


def owner_for_line(line: str, state: UARTFsmState) -> UARTLineOwner:
    """Return semantic owner for a bus line in ``state``."""
    if state is UARTFsmState.IDLE:
        return UARTLineOwner.NONE
    return _ACTIVE_LINE_OWNERS.get(line, UARTLineOwner.NONE)


def transition_on_begin_transmit(current: UARTFsmState) -> UARTFsmState:
    """Idle → start: transmitter pulls line LOW."""
    _require_state(current, UARTFsmState.IDLE)
    return UARTFsmState.START


def transition_after_start_bit(current: UARTFsmState) -> UARTFsmState:
    """Start bit complete → first data bit."""
    _require_state(current, UARTFsmState.START)
    return UARTFsmState.DATA


def transition_after_data_bit(current: UARTFsmState, *, bit_index: int) -> UARTFsmState:
    """Advance data bits; after LSB..MSB (0..7) → stop."""
    _require_state(current, UARTFsmState.DATA)
    if bit_index < 7:
        return UARTFsmState.DATA
    return UARTFsmState.STOP


def transition_after_stop_bit(current: UARTFsmState) -> UARTFsmState:
    """Stop bit complete → idle (line HIGH)."""
    _require_state(current, UARTFsmState.STOP)
    return UARTFsmState.IDLE
