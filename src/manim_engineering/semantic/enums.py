"""Semantic enumerations for pins, signals, and timing."""

from __future__ import annotations

from enum import Enum


class PinDirection(str, Enum):
    """Electrical direction of a pin interface."""

    IN = "in"
    OUT = "out"
    INOUT = "inout"


class SignalDirection(str, Enum):
    """Direction of signal flow relative to source and sink."""

    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


class SignalType(str, Enum):
    """Engineering classification of a signal or pin."""

    DIGITAL = "digital"
    ANALOG = "analog"
    POWER = "power"
    GROUND = "ground"
    CLOCK = "clock"
    DATA = "data"
    SIGNAL = "signal"


class ConnectionState(str, Enum):
    """Whether a pin participates in an explicit connection."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


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
