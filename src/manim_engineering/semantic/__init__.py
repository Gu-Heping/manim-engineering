"""Semantic layer: signals, buses, state, propagation, timing events.

Topology types (``CircuitGraph``, ``Node``, ``Pin``, ``Port``, ``Connection``,
``PinDirection``, ``PortDirection``, ``ConnectionState``, ``SignalType``,
``TopologyError``, ``InvalidConnectionError``, ``InvalidPortError``) live in
``manim_engineering.core`` — import them from there. This package only owns
*semantic* concepts: logic levels, propagation state, timing edges, signal
flow direction, named signals/buses, and the propagation engine.
"""

from manim_engineering.semantic.bus import Bus
from manim_engineering.semantic.enums import (
    LogicLevel,
    PropagationState,
    SignalDirection,
    TimingEdge,
)
from manim_engineering.semantic.exceptions import (
    InvalidPinError,
    PropagationError,
    SemanticError,
)
from manim_engineering.semantic.propagation import (
    PropagationRecord,
    apply_level_between_pins,
    propagate_between_pins,
)
from manim_engineering.semantic.signal import Signal
from manim_engineering.semantic.state import LogicState, TimingEvent
from manim_engineering.semantic.teaching_edges import record_falling_edge, record_rising_edge

__all__ = [
    "Bus",
    "InvalidPinError",
    "LogicLevel",
    "LogicState",
    "PropagationError",
    "PropagationRecord",
    "PropagationState",
    "SemanticError",
    "Signal",
    "SignalDirection",
    "TimingEdge",
    "TimingEvent",
    "apply_level_between_pins",
    "propagate_between_pins",
    "record_falling_edge",
    "record_rising_edge",
]
