"""Semantic enumerations for signals and timing.

Topology enums (``ConnectionState``, ``PinDirection``, ``PortDirection``,
``SignalType``) live in ``manim_engineering.core.enums``.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "LogicLevel",
    "PropagationState",
    "SignalDirection",
    "TimingEdge",
]


class SignalDirection(str, Enum):
    """Direction of signal flow relative to source and sink."""

    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


class LogicLevel(str, Enum):
    """Discrete logic level for digital semantics."""

    LOW = "low"
    HIGH = "high"
    X = "x"
    Z = "z"


class PropagationState(str, Enum):
    """Lifecycle of a propagation step on a signal."""

    IDLE = "idle"
    PROPAGATING = "propagating"
    SETTLED = "settled"


class TimingEdge(str, Enum):
    """Edge type for a timing event."""

    RISING = "rising"
    FALLING = "falling"
