"""Core enumerations for ports and topology."""

from __future__ import annotations

from enum import Enum


class PortDirection(str, Enum):
    """Electrical direction of a port interface."""

    IN = "in"
    OUT = "out"
    INOUT = "inout"


# Backward-compatible alias for existing PinDirection imports.
PinDirection = PortDirection


class SignalType(str, Enum):
    """Engineering classification of a signal or port."""

    DIGITAL = "digital"
    ANALOG = "analog"
    POWER = "power"
    GROUND = "ground"
    CLOCK = "clock"
    DATA = "data"
    SIGNAL = "signal"


class ConnectionState(str, Enum):
    """Whether a port participates in an explicit connection."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
