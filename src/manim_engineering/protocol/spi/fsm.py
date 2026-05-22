"""SPI finite-state machine transitions."""

from __future__ import annotations

from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState


def owner_for_line(line: str, state: SPIFsmState) -> SPIBusOwner:
    """Return semantic owner for a bus line in ``state``."""
    if state is SPIFsmState.IDLE:
        return SPIBusOwner.NONE
    if line == "miso":
        return SPIBusOwner.SLAVE if state is SPIFsmState.TRANSMITTING else SPIBusOwner.NONE
    if line in ("clk", "mosi", "cs"):
        return SPIBusOwner.MASTER
    return SPIBusOwner.NONE


def transition_on_cs_assert(current: SPIFsmState) -> SPIFsmState:
    """Chip select active (LOW): idle → active."""
    if current is SPIFsmState.IDLE:
        return SPIFsmState.ACTIVE
    raise ValueError(f"cannot assert CS from {current.value}")


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
