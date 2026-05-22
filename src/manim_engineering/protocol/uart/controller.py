"""UART controller: deterministic 8N1 byte transmission."""

from __future__ import annotations

from manim_engineering.protocol.uart.binding import UARTBinding
from manim_engineering.protocol.uart.enums import UARTFsmState, UARTLineOwner, UARTRole
from manim_engineering.protocol.uart.fsm import (
    owner_for_line,
    transition_after_data_bit,
    transition_after_start_bit,
    transition_after_stop_bit,
    transition_on_begin_transmit,
)
from manim_engineering.protocol.uart.timing import data_bit_event, start_bit_event, stop_bit_event
from manim_engineering.protocol.uart.transfer import UARTStep, UARTTransferResult
from manim_engineering.semantic import LogicLevel, apply_level_between_pins
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.state import TimingEvent


def _bit_at_lsb(byte_value: int, index: int) -> LogicLevel:
    """LSB-first bit at ``index`` (0 = LSB)."""
    mask = 1 << index
    return LogicLevel.HIGH if (byte_value & mask) else LogicLevel.LOW


class UARTController:
    """
    Semantic UART transmitter: one 8N1 byte per :meth:`transmit_byte`.

    Idle line is HIGH; start LOW; eight data bits LSB-first; one stop HIGH.
    Bit period defaults to 1.0 (educational scale); ``baud_rate`` sets metadata only.
    """

    def __init__(
        self,
        binding: UARTBinding,
        *,
        role: UARTRole = UARTRole.TRANSMITTER,
        baud_rate: float = 9600.0,
        bit_period: float = 1.0,
    ) -> None:
        if role is not UARTRole.TRANSMITTER:
            msg = "UARTController currently implements transmitter-driven frames only"
            raise ValueError(msg)
        if baud_rate <= 0:
            raise ValueError("baud_rate must be positive")
        if bit_period <= 0:
            raise ValueError("bit_period must be positive")
        self._binding = binding
        self._baud_rate = baud_rate
        self._bit_period = bit_period
        self._fsm_state = UARTFsmState.IDLE
        self._time = 0.0

    @property
    def fsm_state(self) -> UARTFsmState:
        return self._fsm_state

    @property
    def role(self) -> UARTRole:
        return UARTRole.TRANSMITTER

    @property
    def baud_rate(self) -> float:
        return self._baud_rate

    @property
    def bit_period(self) -> float:
        return self._bit_period

    def transmit_byte(self, tx_byte: int) -> UARTTransferResult:
        """Transmit one byte 8N1; update ``tx`` signal and emit timing events."""
        if tx_byte < 0 or tx_byte > 0xFF:
            raise ValueError("tx_byte must be 0..255")
        if self._fsm_state is not UARTFsmState.IDLE:
            raise ValueError(f"cannot transmit from {self._fsm_state.value}")

        steps: list[UARTStep] = []
        all_events: list[TimingEvent] = []

        steps.append(self._send_start_bit())
        all_events.extend(steps[-1].timing_events)

        for bit_index in range(8):
            steps.append(self._send_data_bit(tx_byte, bit_index))
            all_events.extend(steps[-1].timing_events)

        steps.append(self._send_stop_bit())
        all_events.extend(steps[-1].timing_events)

        return UARTTransferResult(
            tx_byte=tx_byte,
            steps=tuple(steps),
            timing_events=tuple(all_events),
            final_fsm_state=self._fsm_state,
            bit_period=self._bit_period,
        )

    def _advance_time(self) -> float:
        t = self._time
        self._time += self._bit_period
        return t

    def _line_owners(self) -> dict[str, UARTLineOwner]:
        return {
            "tx": owner_for_line("tx", self._fsm_state),
            "rx": owner_for_line("rx", self._fsm_state),
        }

    def _step(
        self,
        *,
        records: tuple[PropagationRecord, ...],
        timing_events: tuple[TimingEvent, ...],
    ) -> UARTStep:
        return UARTStep(
            time=self._time,
            fsm_state=self._fsm_state,
            line_owner=self._line_owners(),
            records=records,
            timing_events=timing_events,
        )

    def _apply(
        self,
        signal,
        from_pin,
        to_pin,
        level: LogicLevel,
    ) -> PropagationRecord:
        return apply_level_between_pins(
            signal,
            from_pin,
            to_pin,
            level,
            graph=self._binding.graph,
        )

    def _send_start_bit(self) -> UARTStep:
        b = self._binding
        self._fsm_state = transition_on_begin_transmit(self._fsm_state)
        t = self._advance_time()
        rec = self._apply(b.tx, b.transmitter_tx, b.receiver_rx, LogicLevel.LOW)
        self._fsm_state = transition_after_start_bit(self._fsm_state)
        return self._step(
            records=(rec,),
            timing_events=(start_bit_event(t, b.transmitter_tx.id),),
        )

    def _send_data_bit(self, tx_byte: int, bit_index: int) -> UARTStep:
        b = self._binding
        level = _bit_at_lsb(tx_byte, bit_index)
        t = self._advance_time()
        rec = self._apply(b.tx, b.transmitter_tx, b.receiver_rx, level)
        self._fsm_state = transition_after_data_bit(self._fsm_state, bit_index=bit_index)
        return self._step(
            records=(rec,),
            timing_events=(data_bit_event(t, b.transmitter_tx.id, bit_index=bit_index),),
        )

    def _send_stop_bit(self) -> UARTStep:
        b = self._binding
        t = self._advance_time()
        rec = self._apply(b.tx, b.transmitter_tx, b.receiver_rx, LogicLevel.HIGH)
        self._fsm_state = transition_after_stop_bit(self._fsm_state)
        return self._step(
            records=(rec,),
            timing_events=(stop_bit_event(t, b.transmitter_tx.id),),
        )
