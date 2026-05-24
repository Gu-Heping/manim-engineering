"""UART baud-scaled timing events (educational bit periods)."""

from __future__ import annotations

from manim_engineering.semantic.enums import TimingEdge
from manim_engineering.semantic.state import TimingEvent


def _phase_metadata(
    *,
    bit_index: int | None = None,
    phase: float | None = None,
) -> dict[str, float]:
    """Build optional UART bit-index / phase metadata."""
    meta: dict[str, float] = {}
    if bit_index is not None:
        meta["bit_index"] = float(bit_index)
    if phase is not None:
        meta["phase"] = phase
    return meta


def _edge_event(
    *,
    time: float,
    pin_id: str,
    edge: TimingEdge,
    bit_index: int | None = None,
    phase: float | None = None,
) -> TimingEvent:
    """Construct a UART ``TimingEvent`` with optional bit/phase metadata."""
    return TimingEvent(
        time=time,
        edge=edge,
        pin_id=pin_id,
        metadata=_phase_metadata(bit_index=bit_index, phase=phase),
    )


def start_bit_event(time: float, pin_id: str) -> TimingEvent:
    """Falling edge: idle HIGH → start LOW."""
    return _edge_event(time=time, pin_id=pin_id, edge=TimingEdge.FALLING, phase=0.0)


def data_bit_event(time: float, pin_id: str, *, bit_index: int) -> TimingEvent:
    """Bit-period boundary for LSB-first data (``bit_index`` 0 = LSB)."""
    return _edge_event(
        time=time,
        pin_id=pin_id,
        edge=TimingEdge.RISING,
        bit_index=bit_index,
        phase=1.0,
    )


def stop_bit_event(time: float, pin_id: str) -> TimingEvent:
    """Rising edge: final data bit → stop HIGH."""
    return _edge_event(
        time=time,
        pin_id=pin_id,
        edge=TimingEdge.RISING,
        phase=2.0,
    )
