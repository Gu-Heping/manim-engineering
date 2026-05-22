"""CircuitElement base: semantic pins and layout hints without rendering."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from manim_engineering.components.types import Bounds
from manim_engineering.semantic.enums import PinDirection, SignalType
from manim_engineering.semantic.exceptions import InvalidPinError
from manim_engineering.semantic.graph import CircuitGraph
from manim_engineering.semantic.node import Node
from manim_engineering.semantic.pin import Pin

AnchorPoint = tuple[float, float]


class CircuitElement(ABC):
    """Reusable semantic circuit object with pins and layout metadata."""

    semantic_type: ClassVar[str]

    def __init__(
        self,
        element_id: str,
        *,
        label: str | None = None,
    ) -> None:
        self._element_id = element_id
        self.label = label
        self.pins: dict[str, Pin] = {}
        self._register_pins()

    @property
    def element_id(self) -> str:
        """Stable identifier used as pin owner and graph node id."""
        return self._element_id

    @property
    @abstractmethod
    def anchor_points(self) -> dict[str, AnchorPoint]:
        """Named alignment points in component-local coordinates."""

    @property
    @abstractmethod
    def bounds(self) -> Bounds:
        """Axis-aligned footprint for layout and routing."""

    def get_pin(self, name: str) -> Pin:
        """Return a pin by stable lowercase name."""
        try:
            return self.pins[name]
        except KeyError as exc:
            raise InvalidPinError(f"unknown pin {self._element_id}.{name}") from exc

    def get_bounds(self) -> Bounds:
        """Return the component bounding box."""
        return self.bounds

    def to_node(self) -> Node:
        """Build a semantic node sharing this component's pin instances."""
        return Node(
            id=self._element_id,
            label=self.label or "",
            pins=dict(self.pins),
        )

    def attach_to(self, graph: CircuitGraph) -> Node:
        """Register this component as a node in the circuit graph."""
        return graph.add_node(self.to_node())

    def _register_pin(
        self,
        name: str,
        *,
        direction: PinDirection,
        signal_type: SignalType,
        routing_hints: tuple[str, ...] = (),
    ) -> Pin:
        """Create and store a pin owned by this component."""
        if name in self.pins:
            raise InvalidPinError(f"duplicate pin {self._element_id}.{name}")
        pin = Pin(
            name=name,
            owner_id=self._element_id,
            direction=direction,
            signal_type=signal_type,
            routing_hints=routing_hints,
        )
        self.pins[name] = pin
        return pin

    @abstractmethod
    def _register_pins(self) -> None:
        """Subclass hook to define pins after base initialization."""
