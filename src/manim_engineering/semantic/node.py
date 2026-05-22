"""Semantic node in a circuit graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.semantic.enums import PinDirection, SignalType
from manim_engineering.semantic.exceptions import InvalidPinError
from manim_engineering.semantic.pin import Pin


@dataclass
class Node:
    """A named entity that owns pins in the topology."""

    id: str
    label: str = ""
    pins: dict[str, Pin] = field(default_factory=dict)

    def add_pin(
        self,
        name: str,
        *,
        direction: PinDirection,
        signal_type: SignalType,
        routing_hints: tuple[str, ...] = (),
    ) -> Pin:
        """Register a pin on this node and return it."""
        if name in self.pins:
            raise InvalidPinError(f"duplicate pin {self.id}.{name}")
        pin = Pin(
            name=name,
            owner_id=self.id,
            direction=direction,
            signal_type=signal_type,
            routing_hints=routing_hints,
        )
        self.pins[name] = pin
        return pin

    def get_pin(self, name: str) -> Pin:
        """Return a pin by name."""
        try:
            return self.pins[name]
        except KeyError as exc:
            raise InvalidPinError(f"unknown pin {self.id}.{name}") from exc
