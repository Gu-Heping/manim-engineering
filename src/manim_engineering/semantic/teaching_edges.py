"""Teaching helpers for explicit rising/falling edge propagation records."""

from __future__ import annotations

from manim_engineering.core.graph import CircuitGraph
from manim_engineering.core.port import Pin
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.semantic.exceptions import PropagationError
from manim_engineering.semantic.propagation import (
    PropagationRecord,
    apply_level_between_pins,
    propagate_between_pins,
)
from manim_engineering.semantic.signal import Signal


def record_analog_level_between_pins(
    signal: Signal,
    from_pin: Pin,
    to_pin: Pin,
    level: float,
    *,
    graph: CircuitGraph | None = None,
) -> PropagationRecord:
    """Record a float level transition on an analog teaching net."""
    if graph is not None and not graph.are_connected(from_pin, to_pin):
        msg = f"no topology connection between {from_pin.id} and {to_pin.id}"
        raise PropagationError(msg)

    previous = signal.value
    signal.value = level
    signal.source_pin = from_pin
    signal.sink_pin = to_pin

    record = PropagationRecord(
        from_pin_id=from_pin.id,
        to_pin_id=to_pin.id,
        previous_value=previous,
        new_value=level,
        state_transition=f"{previous!r}→{level!r}",
    )
    signal._propagation_history.append(record)
    return record


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
