"""Bus: first-class grouped signal topology."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.semantic.exceptions import TopologyError
from manim_engineering.semantic.graph import CircuitGraph
from manim_engineering.semantic.pin import Pin
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal


@dataclass
class Bus:
    """
    Grouped signals that propagate together across member pins.

    Not decorative parallel lines — synchronized semantic topology.
    """

    name: str
    signals: tuple[Signal, ...] = ()
    member_pins: tuple[Pin, ...] = ()

    def __post_init__(self) -> None:
        if len(self.signals) != len(self.member_pins):
            msg = "signals and member_pins must have the same length"
            raise TopologyError(msg)

    @classmethod
    def from_signals(
        cls,
        name: str,
        pairs: tuple[tuple[Signal, Pin], ...],
    ) -> Bus:
        """Build a bus from (signal, pin) pairs in deterministic order."""
        signals = tuple(pair[0] for pair in pairs)
        pins = tuple(pair[1] for pair in pairs)
        return cls(name=name, signals=signals, member_pins=pins)

    def propagate_lane(
        self,
        lane_index: int,
        from_pin: Pin,
        to_pin: Pin,
        *,
        graph: CircuitGraph | None = None,
    ) -> PropagationRecord:
        """Propagate one lane by index."""
        signal = self.signals[lane_index]
        return signal.propagate(from_pin, to_pin, graph=graph)

    def propagate_all(
        self,
        edges: tuple[tuple[Pin, Pin], ...],
        *,
        graph: CircuitGraph | None = None,
    ) -> tuple[PropagationRecord, ...]:
        """
        Propagate every lane in index order.

        ``edges`` must have one (from_pin, to_pin) pair per signal lane.
        """
        if len(edges) != len(self.signals):
            msg = "edges count must match bus lane count"
            raise TopologyError(msg)
        records: list[PropagationRecord] = []
        for index, (from_pin, to_pin) in enumerate(edges):
            records.append(self.propagate_lane(index, from_pin, to_pin, graph=graph))
        return tuple(records)
