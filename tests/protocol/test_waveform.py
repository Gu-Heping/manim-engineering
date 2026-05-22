"""Waveform bundle derives from SPI protocol signal history."""

from __future__ import annotations

from manim_engineering.protocol.spi import SPIBusBinding, SPIController
from manim_engineering.semantic import CircuitGraph
from manim_engineering.waveform import derive_bundle_from_signals, level_from_value


def test_waveform_matches_signal_after_transfer() -> None:
    binding = SPIBusBinding.create_bus(CircuitGraph())
    SPIController(binding).transfer_byte(0xF0, rx_byte=0x0F)
    bundle = derive_bundle_from_signals(binding.signals(), time_step=1.0)
    for signal in binding.signals():
        trace = bundle.trace_named(signal.name)
        assert trace is not None
        assert trace.samples
        assert level_from_value(signal.value) == trace.samples[-1].level


def test_clk_trace_has_multiple_edges() -> None:
    binding = SPIBusBinding.create_bus(CircuitGraph())
    SPIController(binding).transfer_byte(0x55)
    bundle = derive_bundle_from_signals((binding.clk,))
    trace = bundle.trace_named("clk")
    assert trace is not None
    assert len(trace.samples) >= 3
