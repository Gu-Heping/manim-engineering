"""UART semantic enumerations."""

from __future__ import annotations

from enum import Enum


class UARTFsmState(str, Enum):
    """Deterministic async framing lifecycle."""

    IDLE = "idle"
    START = "start"
    DATA = "data"
    STOP = "stop"


class UARTRole(str, Enum):
    """Device role on the link."""

    TRANSMITTER = "transmitter"
    RECEIVER = "receiver"


class UARTLineOwner(str, Enum):
    """Explicit line ownership (never inferred from visuals)."""

    NONE = "none"
    TRANSMITTER = "transmitter"
    RECEIVER = "receiver"
