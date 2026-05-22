"""SPI mode-0 timing events (clock edges drive sampling)."""

from __future__ import annotations

from manim_engineering.semantic.enums import TimingEdge
from manim_engineering.semantic.state import TimingEvent


def clock_rising_event(
    time: float,
    pin_id: str,
    *,
    bit_index: int | None = None,
) -> TimingEvent:
    """Rising edge: sample MOSI/MISO in mode 0."""
    metadata: dict[str, float] = {}
    if bit_index is not None:
        metadata["bit_index"] = float(bit_index)
    return TimingEvent(time=time, edge=TimingEdge.RISING, pin_id=pin_id, metadata=metadata)


def clock_falling_event(
    time: float,
    pin_id: str,
    *,
    bit_index: int | None = None,
) -> TimingEvent:
    """Falling edge: update MOSI for next bit in mode 0."""
    metadata: dict[str, float] = {}
    if bit_index is not None:
        metadata["bit_index"] = float(bit_index)
    return TimingEvent(time=time, edge=TimingEdge.FALLING, pin_id=pin_id, metadata=metadata)
