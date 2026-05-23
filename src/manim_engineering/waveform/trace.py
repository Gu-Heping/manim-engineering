"""Waveform trace model (semantic projection, no Manim)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.core.enums import SignalType
from manim_engineering.semantic.enums import LogicLevel


@dataclass(frozen=True)
class WaveformSample:
    """One sample on the semantic time axis."""

    time: float
    level: LogicLevel | float


@dataclass(frozen=True)
class WaveformTrace:
    """Discrete or continuous trace for one signal / pin identity."""

    signal_name: str
    signal_type: SignalType
    pin_id: str
    samples: tuple[WaveformSample, ...]
    is_discrete: bool = True

    @property
    def end_time(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].time

    def level_at(self, time: float) -> LogicLevel | float | None:
        """Last sample at or before ``time`` (digital hold)."""
        if not self.samples:
            return None
        held: LogicLevel | float | None = None
        for sample in self.samples:
            if sample.time > time:
                break
            held = sample.level
        return held


@dataclass(frozen=True)
class WaveformBundle:
    """Multiple traces sharing a common semantic time base (e.g. clock + data)."""

    traces: tuple[WaveformTrace, ...]

    def trace_named(self, name: str) -> WaveformTrace | None:
        for trace in self.traces:
            if trace.signal_name == name:
                return trace
        return None
