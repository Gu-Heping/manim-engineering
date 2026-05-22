"""SPI controller: deterministic mode-0 byte transfer."""

from __future__ import annotations

from manim_engineering.protocol.spi.binding import SPIBusBinding
from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState, SPIMode, SPIRole
from manim_engineering.protocol.spi.fsm import (
    owner_for_line,
    transition_on_cs_assert,
    transition_on_cs_deassert,
    transition_on_first_clock_edge,
)
from manim_engineering.protocol.spi.timing import clock_falling_event, clock_rising_event
from manim_engineering.protocol.spi.transfer import SPIStep, SPITransferResult
from manim_engineering.semantic import LogicLevel, apply_level_between_pins
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.state import TimingEvent


def _bit_at(byte_value: int, index: int) -> LogicLevel:
    """MSB-first bit at ``index`` (7 = MSB)."""
    mask = 1 << (7 - index)
    return LogicLevel.HIGH if (byte_value & mask) else LogicLevel.LOW


class SPIController:
    """
    Semantic SPI master: one byte per :meth:`transfer_byte`.

    Mode 0: CPOL=0 (idle LOW), CPHA=0 (sample on rising, change on falling).
    """

    def __init__(
        self,
        binding: SPIBusBinding,
        *,
        role: SPIRole = SPIRole.MASTER,
        mode: SPIMode = SPIMode.MODE_0,
    ) -> None:
        if role is not SPIRole.MASTER:
            msg = "SPIController currently implements master-driven transfers only"
            raise ValueError(msg)
        if mode is not SPIMode.MODE_0:
            msg = f"unsupported SPI mode: {mode.value}"
            raise ValueError(msg)
        self._binding = binding
        self._fsm_state = SPIFsmState.IDLE
        self._time = 0.0
        self._time_step = 1.0

    @property
    def fsm_state(self) -> SPIFsmState:
        return self._fsm_state

    @property
    def role(self) -> SPIRole:
        return SPIRole.MASTER

    def transfer_byte(
        self,
        tx_byte: int,
        *,
        rx_byte: int | None = None,
    ) -> SPITransferResult:
        """
        Transfer one byte MSB-first; update signals and emit timing events.

        ``rx_byte`` sets slave MISO bits sampled on rising edges (defaults to 0).
        """
        if tx_byte < 0 or tx_byte > 0xFF:
            raise ValueError("tx_byte must be 0..255")
        response = 0 if rx_byte is None else rx_byte
        if response < 0 or response > 0xFF:
            raise ValueError("rx_byte must be 0..255")

        steps: list[SPIStep] = []
        all_events: list[TimingEvent] = []

        steps.append(self._assert_cs())
        all_events.extend(steps[-1].timing_events)

        for bit_index in range(8):
            steps.append(self._transfer_bit(tx_byte, response, bit_index))
            all_events.extend(steps[-1].timing_events)

        steps.append(self._deassert_cs())
        all_events.extend(steps[-1].timing_events)

        return SPITransferResult(
            tx_byte=tx_byte,
            rx_byte=response,
            steps=tuple(steps),
            timing_events=tuple(all_events),
            final_fsm_state=self._fsm_state,
        )

    def _advance_time(self) -> float:
        t = self._time
        self._time += self._time_step
        return t

    def _line_owners(self) -> dict[str, SPIBusOwner]:
        return {
            "clk": owner_for_line("clk", self._fsm_state),
            "mosi": owner_for_line("mosi", self._fsm_state),
            "miso": owner_for_line("miso", self._fsm_state),
            "cs": owner_for_line("cs", self._fsm_state),
        }

    def _step(
        self,
        *,
        records: tuple[PropagationRecord, ...],
        timing_events: tuple[TimingEvent, ...],
    ) -> SPIStep:
        return SPIStep(
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

    def _assert_cs(self) -> SPIStep:
        b = self._binding
        self._fsm_state = transition_on_cs_assert(self._fsm_state)
        rec = self._apply(b.cs, b.master_cs, b.slave_cs, LogicLevel.LOW)
        return self._step(records=(rec,), timing_events=())

    def _deassert_cs(self) -> SPIStep:
        b = self._binding
        self._fsm_state = transition_on_cs_deassert(self._fsm_state)
        rec = self._apply(b.cs, b.master_cs, b.slave_cs, LogicLevel.HIGH)
        return self._step(records=(rec,), timing_events=())

    def _transfer_bit(self, tx_byte: int, rx_byte: int, bit_index: int) -> SPIStep:
        b = self._binding
        records: list[PropagationRecord] = []
        events: list[TimingEvent] = []

        mosi_level = _bit_at(tx_byte, bit_index)
        rec_mosi = self._apply(b.mosi, b.master_mosi, b.slave_mosi, mosi_level)
        records.append(rec_mosi)

        if self._fsm_state is SPIFsmState.ACTIVE:
            self._fsm_state = transition_on_first_clock_edge(self._fsm_state)
        else:
            self._fsm_state = SPIFsmState.TRANSMITTING

        t_rise = self._advance_time()
        rec_clk_hi = self._apply(b.clk, b.master_clk, b.slave_clk, LogicLevel.HIGH)
        records.append(rec_clk_hi)
        events.append(
            clock_rising_event(t_rise, b.master_clk.id, bit_index=bit_index),
        )

        miso_level = _bit_at(rx_byte, bit_index)
        rec_miso = self._apply(b.miso, b.slave_miso, b.master_miso, miso_level)
        records.append(rec_miso)

        t_fall = self._advance_time()
        rec_clk_lo = self._apply(b.clk, b.master_clk, b.slave_clk, LogicLevel.LOW)
        records.append(rec_clk_lo)
        events.append(
            clock_falling_event(t_fall, b.master_clk.id, bit_index=bit_index),
        )

        return self._step(
            records=tuple(records),
            timing_events=tuple(events),
        )
