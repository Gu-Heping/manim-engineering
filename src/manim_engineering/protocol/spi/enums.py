"""SPI semantic enumerations."""

from __future__ import annotations

from enum import Enum


class SPIFsmState(str, Enum):
    """Deterministic protocol lifecycle."""

    IDLE = "idle"
    ACTIVE = "active"
    TRANSMITTING = "transmitting"


class SPIRole(str, Enum):
    """Device role on the bus."""

    MASTER = "master"
    SLAVE = "slave"


class SPIMode(str, Enum):
    """Clock polarity / phase (mode 0: CPOL=0, CPHA=0)."""

    MODE_0 = "mode_0"


class SPIBusOwner(str, Enum):
    """Explicit bus line ownership (never inferred from visuals)."""

    NONE = "none"
    MASTER = "master"
    SLAVE = "slave"
