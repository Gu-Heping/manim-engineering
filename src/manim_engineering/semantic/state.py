"""Logic and timing state for semantic simulation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from manim_engineering.semantic.enums import LogicLevel, TimingEdge


def _level_label(level: LogicLevel) -> str:
    """Stable string label for transition text (matches enum value)."""
    return level.value


@dataclass(frozen=True)
class LogicState:
    """Explicit logic level with optional analog voltage."""

    level: LogicLevel
    voltage: float | None = None

    def transition_label(self, other: LogicState) -> str:
        """Human-readable transition label, e.g. ``LOW→HIGH``."""
        return f"{_level_label(self.level)}→{_level_label(other.level)}"

    def __repr__(self) -> str:
        if self.voltage is None:
            return f"LogicState(level={self.level!r})"
        return f"LogicState(level={self.level!r}, voltage={self.voltage!r})"


@dataclass(frozen=True)
class TimingEvent:
    """A timing edge or sample point bound to a pin."""

    time: float
    edge: TimingEdge
    pin_id: str
    metadata: Mapping[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        meta = dict(self.metadata)
        if meta:
            return (
                f"TimingEvent(time={self.time!r}, edge={self.edge!r}, "
                f"pin_id={self.pin_id!r}, metadata={meta!r})"
            )
        return (
            f"TimingEvent(time={self.time!r}, edge={self.edge!r}, pin_id={self.pin_id!r})"
        )
