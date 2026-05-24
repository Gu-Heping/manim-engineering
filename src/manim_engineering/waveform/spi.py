"""SPI waveform bundle on the controller's global time axis."""

from __future__ import annotations

from manim_engineering.protocol.spi.binding import SPIBusBinding
from manim_engineering.protocol.spi.transfer import SPITransferResult
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.derive import level_from_value
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace


def _record_signal_name(binding: SPIBusBinding, record: PropagationRecord) -> str:
    for signal in binding.signals():
        if record in signal.propagation_history:
            return signal.name
    msg = f"propagation record not found on SPI bus: {record.to_pin_id}"
    raise ValueError(msg)


def _resolve_pin_id(signal: Signal) -> str:
    if signal.sink_pin is not None:
        return signal.sink_pin.id
    if signal.source_pin is not None:
        return signal.source_pin.id
    return signal.name


def derive_spi_waveform_bundle(
    binding: SPIBusBinding,
    result: SPITransferResult,
) -> WaveformBundle:
    """Build clk/mosi/miso/cs traces sharing ``SPIController`` event times."""
    signals = binding.signals()
    buckets: dict[str, list[WaveformSample]] = {signal.name: [] for signal in signals}

    def push(name: str, time: float, level: LogicLevel | float) -> None:
        samples = buckets[name]
        if samples and samples[-1].time == time and samples[-1].level == level:
            return
        samples.append(WaveformSample(time=time, level=level))

    for signal in signals:
        history = signal.propagation_history
        if not history:
            continue
        initial = level_from_value(history[0].previous_value)
        if initial is not None:
            push(signal.name, 0.0, initial)

    for step in result.steps:
        if not step.timing_events:
            for record in step.records:
                level = level_from_value(record.new_value)
                if level is not None:
                    push(_record_signal_name(binding, record), step.time, level)
            continue

        rise_t = step.timing_events[0].time
        fall_t = step.timing_events[1].time
        bit_times = (rise_t, rise_t, rise_t, fall_t)
        for record, event_time in zip(step.records, bit_times, strict=True):
            level = level_from_value(record.new_value)
            if level is not None:
                push(_record_signal_name(binding, record), event_time, level)

    traces = tuple(
        WaveformTrace(
            signal_name=signal.name,
            signal_type=signal.signal_type,
            pin_id=_resolve_pin_id(signal),
            samples=tuple(buckets[signal.name]),
            is_discrete=True,
        )
        for signal in signals
    )
    return WaveformBundle(traces=traces)
