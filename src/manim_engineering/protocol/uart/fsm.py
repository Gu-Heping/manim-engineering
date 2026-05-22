"""UART finite-state machine transitions."""

from __future__ import annotations

from manim_engineering.protocol.uart.enums import UARTFsmState, UARTLineOwner


def owner_for_line(line: str, state: UARTFsmState) -> UARTLineOwner:
    """Return semantic owner for a bus line in ``state``."""
    if state is UARTFsmState.IDLE:
        return UARTLineOwner.NONE
    if line == "tx":
        return UARTLineOwner.TRANSMITTER
    if line == "rx":
        return UARTLineOwner.RECEIVER
    return UARTLineOwner.NONE


def transition_on_begin_transmit(current: UARTFsmState) -> UARTFsmState:
    """Idle → start: transmitter pulls line LOW."""
    if current is UARTFsmState.IDLE:
        return UARTFsmState.START
    raise ValueError(f"cannot begin transmit from {current.value}")


def transition_after_start_bit(current: UARTFsmState) -> UARTFsmState:
    """Start bit complete → first data bit."""
    if current is UARTFsmState.START:
        return UARTFsmState.DATA
    raise ValueError(f"cannot leave start from {current.value}")


def transition_after_data_bit(current: UARTFsmState, *, bit_index: int) -> UARTFsmState:
    """Advance data bits; after LSB..MSB (0..7) → stop."""
    if current is not UARTFsmState.DATA:
        raise ValueError(f"cannot advance data from {current.value}")
    if bit_index < 7:
        return UARTFsmState.DATA
    return UARTFsmState.STOP


def transition_after_stop_bit(current: UARTFsmState) -> UARTFsmState:
    """Stop bit complete → idle (line HIGH)."""
    if current is UARTFsmState.STOP:
        return UARTFsmState.IDLE
    raise ValueError(f"cannot finish stop from {current.value}")
