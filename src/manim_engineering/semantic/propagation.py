"""Explicit, deterministic signal propagation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from manim_engineering.core.enums import SignalType
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.core.port import Pin
from manim_engineering.semantic.enums import LogicLevel, PropagationState
from manim_engineering.semantic.exceptions import PropagationError
from manim_engineering.semantic.state import LogicState

if TYPE_CHECKING:
    from manim_engineering.semantic.signal import Signal


@dataclass(frozen=True)
class PropagationRecord:
    """Immutable record of one propagation step."""

    from_pin_id: str
    to_pin_id: str
    previous_value: LogicState | float | None
    new_value: LogicState | float | None
    state_transition: str


def _logic_from_value(value: LogicState | float | None) -> LogicState | None:
    if isinstance(value, LogicState):
        return value
    return None


def _resolve_propagated_value(
    value: LogicState | float | None,
    signal_type: SignalType,
) -> LogicState | float | None:
    """Derive the value after propagation (minimal digital edge for LOW)."""
    if isinstance(value, LogicState):
        if value.level == LogicLevel.LOW and signal_type in (
            SignalType.DIGITAL,
            SignalType.CLOCK,
            SignalType.DATA,
        ):
            return LogicState(level=LogicLevel.HIGH, voltage=value.voltage)
        return LogicState(level=value.level, voltage=value.voltage)
    if isinstance(value, float):
        return value
    return None


def _transition_label(
    previous: LogicState | float | None,
    new: LogicState | float | None,
) -> str:
    prev_logic = _logic_from_value(previous)
    new_logic = _logic_from_value(new)
    if prev_logic is not None and new_logic is not None:
        return prev_logic.transition_label(new_logic)
    if previous == new:
        return "unchanged"
    return f"{previous!r}→{new!r}"


def apply_level_between_pins(
    signal: Signal,
    from_pin: Pin,
    to_pin: Pin,
    level: LogicLevel,
    *,
    graph: CircuitGraph | None = None,
    voltage: float | None = None,
) -> PropagationRecord:
    """
    Set ``signal`` to an explicit logic level and record the transition.

    Used by protocol FSMs that need arbitrary bit sequences (not only LOW→HIGH toggle).
    """
    if graph is not None and not graph.are_connected(from_pin, to_pin):
        raise PropagationError(f"no topology connection between {from_pin.id} and {to_pin.id}")

    previous = signal.value
    new_value = LogicState(level=level, voltage=voltage)

    signal.propagation_state = PropagationState.PROPAGATING
    signal.value = new_value
    signal.source_pin = from_pin
    signal.sink_pin = to_pin
    signal.propagation_state = PropagationState.SETTLED

    record = PropagationRecord(
        from_pin_id=from_pin.id,
        to_pin_id=to_pin.id,
        previous_value=previous,
        new_value=new_value,
        state_transition=_transition_label(previous, new_value),
    )
    signal._propagation_history.append(record)
    return record


def propagate_between_pins(
    signal: Signal,
    from_pin: Pin,
    to_pin: Pin,
    *,
    graph: CircuitGraph | None = None,
) -> PropagationRecord:
    """
    Propagate ``signal`` from ``from_pin`` to ``to_pin``.

    Validates optional graph connectivity. Updates signal value and endpoints.
    """
    if graph is not None and not graph.are_connected(from_pin, to_pin):
        raise PropagationError(f"no topology connection between {from_pin.id} and {to_pin.id}")

    previous = signal.value
    new_value = _resolve_propagated_value(previous, signal.signal_type)

    signal.propagation_state = PropagationState.PROPAGATING
    signal.value = new_value
    signal.source_pin = from_pin
    signal.sink_pin = to_pin
    signal.propagation_state = PropagationState.SETTLED

    record = PropagationRecord(
        from_pin_id=from_pin.id,
        to_pin_id=to_pin.id,
        previous_value=previous,
        new_value=new_value,
        state_transition=_transition_label(previous, new_value),
    )
    signal._propagation_history.append(record)
    return record
