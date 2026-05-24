"""Logic and timing state for semantic simulation."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.semantic.enums import LogicLevel, TimingEdge


def _level_label(level: LogicLevel) -> str:
    """Return the enum value string used in transition labels."""
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
    metadata: dict[str, float] = field(default_factory=dict)
