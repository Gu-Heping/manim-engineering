"""Signal: engineering meaning with explicit propagation."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.core.enums import SignalType
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.core.port import Pin
from manim_engineering.semantic.enums import PropagationState, SignalDirection
from manim_engineering.semantic.propagation import PropagationRecord, propagate_between_pins
from manim_engineering.semantic.state import LogicState


@dataclass
class Signal:
    """
    Engineering signal: type, value, direction, endpoints, timing, propagation state.

    Does not depend on rendering or animation.
    """

    name: str
    signal_type: SignalType
    value: LogicState | float | None = None
    direction: SignalDirection = SignalDirection.FORWARD
    source_pin: Pin | None = None
    sink_pin: Pin | None = None
    timing_metadata: dict[str, float] = field(default_factory=dict)
    propagation_state: PropagationState = PropagationState.IDLE
    _propagation_history: list[PropagationRecord] = field(default_factory=list, repr=False)

    @property
    def propagation_history(self) -> tuple[PropagationRecord, ...]:
        """Immutable view of propagation steps in order."""
        return tuple(self._propagation_history)

    def propagate(
        self,
        from_pin: Pin,
        to_pin: Pin,
        *,
        graph: CircuitGraph | None = None,
    ) -> PropagationRecord:
        """Propagate this signal from ``from_pin`` to ``to_pin``."""
        return propagate_between_pins(self, from_pin, to_pin, graph=graph)
