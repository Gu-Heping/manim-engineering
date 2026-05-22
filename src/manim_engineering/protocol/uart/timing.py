"""UART baud-scaled timing events (educational bit periods)."""

from __future__ import annotations

from manim_engineering.semantic.enums import TimingEdge
from manim_engineering.semantic.state import TimingEvent


def _metadata(*, bit_index: int | None = None, phase: float | None = None) -> dict[str, float]:
    meta: dict[str, float] = {}
    if bit_index is not None:
        meta["bit_index"] = float(bit_index)
    if phase is not None:
        meta["phase"] = phase
    return meta


def start_bit_event(time: float, pin_id: str) -> TimingEvent:
    """Falling edge: idle HIGH → start LOW."""
    return TimingEvent(
        time=time,
        edge=TimingEdge.FALLING,
        pin_id=pin_id,
        metadata=_metadata(phase=0.0),
    )


def data_bit_event(time: float, pin_id: str, *, bit_index: int) -> TimingEvent:
    """Bit-period boundary for LSB-first data (``bit_index`` 0 = LSB)."""
    return TimingEvent(
        time=time,
        edge=TimingEdge.RISING,
        pin_id=pin_id,
        metadata=_metadata(bit_index=bit_index, phase=1.0),
    )


def stop_bit_event(time: float, pin_id: str) -> TimingEvent:
    """Rising edge: final data bit → stop HIGH."""
    return TimingEvent(
        time=time,
        edge=TimingEdge.RISING,
        pin_id=pin_id,
        metadata=_metadata(phase=2.0),
    )
