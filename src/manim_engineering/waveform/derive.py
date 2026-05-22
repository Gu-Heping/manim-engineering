"""Derive waveform samples from signal state and propagation history."""

from __future__ import annotations

from collections.abc import Sequence

from manim_engineering.semantic.enums import LogicLevel, SignalType, TimingEdge
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.semantic.state import LogicState, TimingEvent
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace


def level_from_value(value: LogicState | float | None) -> LogicLevel | float | None:
    if isinstance(value, LogicState):
        return value.level
    if isinstance(value, float):
        return value
    return None


def _is_discrete_signal(signal_type: SignalType) -> bool:
    return signal_type in (
        SignalType.DIGITAL,
        SignalType.CLOCK,
        SignalType.DATA,
    )


def _resolve_pin_id(signal: Signal, pin_id: str | None) -> str:
    if pin_id is not None:
        return pin_id
    if signal.sink_pin is not None:
        return signal.sink_pin.id
    if signal.source_pin is not None:
        return signal.source_pin.id
    return signal.name


def timing_events_from_propagation(signal: Signal) -> tuple[TimingEvent, ...]:
    """Build timing edges from propagation records (semantic, deterministic)."""
    events: list[TimingEvent] = []
    for index, record in enumerate(signal.propagation_history):
        prev = level_from_value(record.previous_value)
        new = level_from_value(record.new_value)
        if prev is None or new is None:
            continue
        if isinstance(prev, LogicLevel) and isinstance(new, LogicLevel):
            if prev == LogicLevel.LOW and new == LogicLevel.HIGH:
                edge = TimingEdge.RISING
            elif prev == LogicLevel.HIGH and new == LogicLevel.LOW:
                edge = TimingEdge.FALLING
            else:
                continue
            events.append(
                TimingEvent(
                    time=float(index + 1),
                    edge=edge,
                    pin_id=record.to_pin_id,
                )
            )
    return tuple(events)


def derive_trace_from_signal(
    signal: Signal,
    *,
    time_step: float = 1.0,
    t0: float = 0.0,
    pin_id: str | None = None,
) -> WaveformTrace:
    """
    Derive trace samples from propagation history and current signal value.

    Does not mutate ``signal`` or topology.
    """
    resolved_pin = _resolve_pin_id(signal, pin_id)
    history = signal.propagation_history
    samples: list[WaveformSample] = []

    if not history:
        level = level_from_value(signal.value)
        if level is not None:
            samples.append(WaveformSample(time=t0, level=level))
        return WaveformTrace(
            signal_name=signal.name,
            signal_type=signal.signal_type,
            pin_id=resolved_pin,
            samples=tuple(samples),
            is_discrete=_is_discrete_signal(signal.signal_type),
        )

    initial = level_from_value(history[0].previous_value)
    if initial is not None:
        samples.append(WaveformSample(time=t0, level=initial))

    for index, record in enumerate(history):
        level = level_from_value(record.new_value)
        if level is not None:
            samples.append(WaveformSample(time=t0 + (index + 1) * time_step, level=level))

    return WaveformTrace(
        signal_name=signal.name,
        signal_type=signal.signal_type,
        pin_id=resolved_pin,
        samples=tuple(samples),
        is_discrete=_is_discrete_signal(signal.signal_type),
    )


def derive_bundle_from_signals(
    signals: Sequence[Signal],
    *,
    time_step: float = 1.0,
    t0: float = 0.0,
) -> WaveformBundle:
    """Build a multi-trace bundle (e.g. clock + data) from semantic signals."""
    traces = tuple(
        derive_trace_from_signal(signal, time_step=time_step, t0=t0) for signal in signals
    )
    return WaveformBundle(traces=traces)


def record_for_beat(signal: Signal, beat: int) -> PropagationRecord | None:
    """Return propagation record at ``beat`` index, or ``None`` if out of range."""
    history = signal.propagation_history
    if not history:
        return None
    if beat < 0:
        beat = len(history) + beat
    if beat < 0 or beat >= len(history):
        return None
    return history[beat]
