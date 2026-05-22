"""SPI byte transfer ordering and determinism."""

from __future__ import annotations

from manim_engineering.protocol.spi import SPIBusBinding, SPIController, SPIFsmState
from manim_engineering.semantic import CircuitGraph, LogicLevel, TimingEdge


def _binding() -> SPIBusBinding:
    return SPIBusBinding.create_bus(CircuitGraph())


def test_transfer_ends_idle_with_cs_high() -> None:
    binding = _binding()
    controller = SPIController(binding)
    result = controller.transfer_byte(0xA5, rx_byte=0x3C)
    assert result.final_fsm_state is SPIFsmState.IDLE
    assert binding.cs.value is not None
    assert binding.cs.value.level is LogicLevel.HIGH


def test_eight_clock_rising_edges_per_byte() -> None:
    binding = _binding()
    result = SPIController(binding).transfer_byte(0x00)
    rising = [e for e in result.timing_events if e.edge is TimingEdge.RISING]
    assert len(rising) == 8


def test_transfer_is_deterministic() -> None:
    def run() -> tuple[int, ...]:
        binding = SPIBusBinding.create_bus(CircuitGraph())
        result = SPIController(binding).transfer_byte(0x5A, rx_byte=0xA5)
        mosi_levels = tuple(
            r.new_value.level
            for r in binding.mosi.propagation_history
            if r.new_value is not None
        )
        return (len(result.steps), len(result.timing_events), len(mosi_levels))

    assert run() == run()


def test_msb_first_mosi_first_bit_is_msb() -> None:
    binding = _binding()
    SPIController(binding).transfer_byte(0x80)
    first_mosi = binding.mosi.propagation_history[0]
    assert first_mosi.new_value is not None
    assert first_mosi.new_value.level is LogicLevel.HIGH


def test_step_fsm_sequence() -> None:
    binding = _binding()
    result = SPIController(binding).transfer_byte(0x01)
    states = [step.fsm_state for step in result.steps]
    assert states[0] is SPIFsmState.ACTIVE
    assert SPIFsmState.TRANSMITTING in states
    assert states[-1] is SPIFsmState.IDLE
