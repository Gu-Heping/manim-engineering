"""SPI mode-0 timing events (clock edges drive sampling)."""

from __future__ import annotations

from manim_engineering.semantic.enums import TimingEdge
from manim_engineering.semantic.state import TimingEvent


def _bit_metadata(*, bit_index: int | None) -> dict[str, float]:
    """Build optional SPI bit-index metadata for a timing edge."""
    if bit_index is None:
        return {}
    return {"bit_index": float(bit_index)}


def _edge_event(
    *,
    time: float,
    pin_id: str,
    edge: TimingEdge,
    bit_index: int | None,
) -> TimingEvent:
    """Construct a mode-0 clock edge ``TimingEvent`` with optional bit metadata."""
    return TimingEvent(
        time=time,
        edge=edge,
        pin_id=pin_id,
        metadata=_bit_metadata(bit_index=bit_index),
    )


def clock_rising_event(
    time: float,
    pin_id: str,
    *,
    bit_index: int | None = None,
) -> TimingEvent:
    """Rising edge: sample MOSI/MISO in mode 0."""
    return _edge_event(
        time=time,
        pin_id=pin_id,
        edge=TimingEdge.RISING,
        bit_index=bit_index,
    )


def clock_falling_event(
    time: float,
    pin_id: str,
    *,
    bit_index: int | None = None,
) -> TimingEvent:
    """Falling edge: update MOSI for next bit in mode 0."""
    return _edge_event(
        time=time,
        pin_id=pin_id,
        edge=TimingEdge.FALLING,
        bit_index=bit_index,
    )
