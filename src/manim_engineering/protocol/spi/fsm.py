"""SPI finite-state machine transitions."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState

# Master-driven lines whenever the bus leaves idle (miso is special-cased below).
_MASTER_LINES: Final[frozenset[str]] = frozenset({"clk", "mosi", "cs"})

# Line ownership during bit transfer (miso driven by slave).
_TRANSMITTING_LINE_OWNERS: Final[MappingProxyType[str, SPIBusOwner]] = MappingProxyType(
    {
        "clk": SPIBusOwner.MASTER,
        "mosi": SPIBusOwner.MASTER,
        "cs": SPIBusOwner.MASTER,
        "miso": SPIBusOwner.SLAVE,
    }
)


def _require_state(current: SPIFsmState, expected: SPIFsmState, *, action: str) -> None:
    """Raise ``ValueError`` when ``current`` is not the expected FSM state."""
    if current is not expected:
        raise ValueError(f"cannot {action} from {current.value}")


def owner_for_line(line: str, state: SPIFsmState) -> SPIBusOwner:
    """Return semantic owner for a bus line in ``state``."""
    if state is SPIFsmState.IDLE:
        return SPIBusOwner.NONE
    if state is SPIFsmState.TRANSMITTING:
        return _TRANSMITTING_LINE_OWNERS.get(line, SPIBusOwner.NONE)
    if state is SPIFsmState.ACTIVE and line in _MASTER_LINES:
        return SPIBusOwner.MASTER
    return SPIBusOwner.NONE


def transition_on_cs_assert(current: SPIFsmState) -> SPIFsmState:
    """Chip select active (LOW): idle → active."""
    _require_state(current, SPIFsmState.IDLE, action="assert CS")
    return SPIFsmState.ACTIVE


def transition_on_first_clock_edge(current: SPIFsmState) -> SPIFsmState:
    """First rising clock edge in a frame: active → transmitting."""
    if current is SPIFsmState.ACTIVE:
        return SPIFsmState.TRANSMITTING
    if current is SPIFsmState.TRANSMITTING:
        return SPIFsmState.TRANSMITTING
    raise ValueError(f"cannot start clock from {current.value}")


def transition_on_cs_deassert(current: SPIFsmState) -> SPIFsmState:
    """Chip select inactive (HIGH): active/transmitting → idle."""
    if current in (SPIFsmState.ACTIVE, SPIFsmState.TRANSMITTING):
        return SPIFsmState.IDLE
    raise ValueError(f"cannot deassert CS from {current.value}")
