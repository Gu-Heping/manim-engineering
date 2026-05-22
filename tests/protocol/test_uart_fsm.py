"""UART FSM determinism, framing, and ownership."""

from __future__ import annotations

import pytest

from manim_engineering.protocol.uart.enums import UARTFsmState, UARTLineOwner
from manim_engineering.protocol.uart.fsm import (
    owner_for_line,
    transition_after_data_bit,
    transition_after_start_bit,
    transition_after_stop_bit,
    transition_on_begin_transmit,
)


def test_begin_transmit_idle_to_start() -> None:
    assert transition_on_begin_transmit(UARTFsmState.IDLE) is UARTFsmState.START


def test_begin_transmit_invalid_from_data() -> None:
    with pytest.raises(ValueError):
        transition_on_begin_transmit(UARTFsmState.DATA)


def test_start_to_data() -> None:
    assert transition_after_start_bit(UARTFsmState.START) is UARTFsmState.DATA


def test_data_bits_stay_until_msb() -> None:
    assert transition_after_data_bit(UARTFsmState.DATA, bit_index=0) is UARTFsmState.DATA
    assert transition_after_data_bit(UARTFsmState.DATA, bit_index=6) is UARTFsmState.DATA
    assert transition_after_data_bit(UARTFsmState.DATA, bit_index=7) is UARTFsmState.STOP


def test_stop_to_idle() -> None:
    assert transition_after_stop_bit(UARTFsmState.STOP) is UARTFsmState.IDLE


def test_transmitter_owns_tx_during_frame() -> None:
    assert owner_for_line("tx", UARTFsmState.START) is UARTLineOwner.TRANSMITTER
    assert owner_for_line("tx", UARTFsmState.DATA) is UARTLineOwner.TRANSMITTER
    assert owner_for_line("tx", UARTFsmState.IDLE) is UARTLineOwner.NONE


def test_receiver_owns_rx_while_active() -> None:
    assert owner_for_line("rx", UARTFsmState.DATA) is UARTLineOwner.RECEIVER
    assert owner_for_line("rx", UARTFsmState.IDLE) is UARTLineOwner.NONE
