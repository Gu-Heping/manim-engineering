"""Teaching helpers for explicit rising/falling edge propagation records."""

from __future__ import annotations

from manim_engineering.core.graph import CircuitGraph
from manim_engineering.core.port import Pin
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.semantic.propagation import (
    PropagationRecord,
    apply_level_between_pins,
    propagate_between_pins,
)
from manim_engineering.semantic.signal import Signal


def record_rising_edge(
    signal: Signal,
    from_pin: Pin,
    to_pin: Pin,
    *,
    graph: CircuitGraph | None = None,
) -> PropagationRecord:
    """Record LOW→HIGH on a connected net (digital / clock / data)."""
    return propagate_between_pins(signal, from_pin, to_pin, graph=graph)


def record_falling_edge(
    signal: Signal,
    from_pin: Pin,
    to_pin: Pin,
    *,
    graph: CircuitGraph | None = None,
) -> PropagationRecord:
    """Record an explicit HIGH→LOW transition on a connected net."""
    return apply_level_between_pins(
        signal,
        from_pin,
        to_pin,
        LogicLevel.LOW,
        graph=graph,
    )
