"""UART byte transfer: framing, LSB-first, determinism."""

from __future__ import annotations

from manim_engineering.protocol.uart import UARTBinding, UARTController, UARTFsmState
from manim_engineering.core import CircuitGraph
from manim_engineering.semantic import LogicLevel


def _binding() -> UARTBinding:
    return UARTBinding.create_bus(CircuitGraph())


def test_transmit_ends_idle_with_line_high() -> None:
    binding = _binding()
    result = UARTController(binding).transmit_byte(0xA5)
    assert result.final_fsm_state is UARTFsmState.IDLE
    assert binding.tx.value is not None
    assert binding.tx.value.level is LogicLevel.HIGH


def test_ten_timing_events_per_byte() -> None:
    """Start + 8 data + stop."""
    binding = _binding()
    result = UARTController(binding).transmit_byte(0x00)
    assert len(result.timing_events) == 10


def test_transfer_is_deterministic() -> None:
    def run() -> tuple[int, ...]:
        binding = UARTBinding.create_bus(CircuitGraph())
        result = UARTController(binding).transmit_byte(0x5A)
        levels = tuple(
            r.new_value.level for r in binding.tx.propagation_history if r.new_value is not None
        )
        return (len(result.steps), len(result.timing_events), len(levels))

    assert run() == run()


def test_lsb_first_first_data_bit_is_lsb() -> None:
    binding = _binding()
    UARTController(binding).transmit_byte(0x01)
    # start LOW, then bit0=1
    data_records = binding.tx.propagation_history[1:9]
    assert data_records[0].new_value is not None
    assert data_records[0].new_value.level is LogicLevel.HIGH


def test_start_bit_is_low() -> None:
    binding = _binding()
    UARTController(binding).transmit_byte(0xFF)
    first = binding.tx.propagation_history[0]
    assert first.new_value is not None
    assert first.new_value.level is LogicLevel.LOW


def test_step_fsm_sequence() -> None:
    binding = _binding()
    result = UARTController(binding).transmit_byte(0x55)
    states = [step.fsm_state for step in result.steps]
    assert states[0] is UARTFsmState.DATA  # start bit applied → DATA
    assert UARTFsmState.STOP in states
    assert states[-1] is UARTFsmState.IDLE


def test_bit_index_metadata_lsb_first() -> None:
    binding = _binding()
    result = UARTController(binding).transmit_byte(0xAA)
    data_events = [e for e in result.timing_events if e.metadata.get("phase") == 1.0]
    assert len(data_events) == 8
    indices = [int(e.metadata["bit_index"]) for e in data_events]
    assert indices == list(range(8))
