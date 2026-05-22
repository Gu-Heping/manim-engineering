"""Waveform bundle derives from UART protocol signal history."""

from __future__ import annotations

from manim_engineering.protocol.uart import UARTBinding, UARTController
from manim_engineering.semantic import CircuitGraph
from manim_engineering.waveform import derive_bundle_from_signals, level_from_value


def test_waveform_matches_signal_after_transmit() -> None:
    binding = UARTBinding.create_bus(CircuitGraph())
    UARTController(binding).transmit_byte(0xF0)
    bundle = derive_bundle_from_signals(binding.signals(), time_step=1.0)
    trace = bundle.trace_named("tx")
    assert trace is not None
    assert trace.samples
    assert level_from_value(binding.tx.value) == trace.samples[-1].level


def test_tx_trace_has_frame_edges() -> None:
    binding = UARTBinding.create_bus(CircuitGraph())
    UARTController(binding).transmit_byte(0x55)
    bundle = derive_bundle_from_signals((binding.tx,))
    trace = bundle.trace_named("tx")
    assert trace is not None
    assert len(trace.samples) >= 3
