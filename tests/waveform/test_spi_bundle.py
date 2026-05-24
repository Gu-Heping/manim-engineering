"""SPI bundle uses controller-global sample times."""

from __future__ import annotations

from manim_engineering.core import CircuitGraph
from manim_engineering.layout.types import Point2D
from manim_engineering.protocol.spi import SPIBusBinding, SPIController
from manim_engineering.waveform import beat_for_time, derive_spi_waveform_bundle
from manim_engineering.waveform.layout import WaveformPanelSpec, step_polyline


def test_spi_bundle_aligns_trace_extent_at_shared_time() -> None:
    binding = SPIBusBinding.create_bus(CircuitGraph())
    result = SPIController(binding).transfer_byte(0xA5, rx_byte=0x3C)
    bundle = derive_spi_waveform_bundle(binding, result)
    spec = WaveformPanelSpec(
        origin=Point2D(0.0, -2.0),
        width=8.0,
        trace_height=0.4,
        trace_gap=0.5,
        time_scale=1.0,
    )
    reveal_time = 2.0
    end_x = spec.origin.x + reveal_time * spec.time_scale
    for trace_index, trace in enumerate(bundle.traces):
        beat = beat_for_time(trace, reveal_time)
        points = step_polyline(
            trace,
            spec,
            trace_index,
            max_beat=beat,
            extend_to_panel=False,
            hold_through_time=reveal_time,
        )
        assert points[-1].x == end_x
