"""CircuitElement base: semantic pins and layout hints without rendering."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from manim_engineering.components.types import Bounds
from manim_engineering.core import CircuitGraph, Node, Port
from manim_engineering.core.enums import PortDirection, SignalType
from manim_engineering.core.exceptions import InvalidPortError
from manim_engineering.core.exceptions import InvalidPortError as InvalidPinError

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
        self.pins: dict[str, Port] = {}
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

    @property
    def ports(self) -> dict[str, Port]:
        """Ports owned by this element (alias for ``pins``)."""
        return self.pins

    def get_port(self, name: str) -> Port:
        """Return a port by stable lowercase name."""
        try:
            return self.pins[name]
        except KeyError as exc:
            raise InvalidPortError(f"unknown port {self._element_id}.{name}") from exc

    def get_pin(self, name: str) -> Port:
        """Backward-compatible alias for :meth:`get_port`."""
        try:
            return self.get_port(name)
        except InvalidPortError as exc:
            raise InvalidPinError(str(exc)) from exc

    def get_bounds(self) -> Bounds:
        """Return the component bounding box."""
        return self.bounds

    def to_node(self) -> Node:
        """Build a semantic node sharing this component's port instances."""
        return Node(
            id=self._element_id,
            label=self.label or "",
            ports=dict(self.pins),
        )

    def attach_to(self, graph: CircuitGraph) -> Node:
        """Register this component as a node in the circuit graph."""
        return graph.add(self)

    def register_in(self, graph: CircuitGraph) -> Node:
        """Alias for :meth:`attach_to`."""
        return graph.add(self)

    def _register_pin(
        self,
        name: str,
        *,
        direction: PortDirection,
        signal_type: SignalType,
        routing_hints: tuple[str, ...] = (),
    ) -> Port:
        """Create and store a port owned by this component."""
        if name in self.pins:
            raise InvalidPortError(f"duplicate port {self._element_id}.{name}")
        port = Port(
            name=name,
            owner_id=self._element_id,
            direction=direction,
            signal_type=signal_type,
            routing_hints=routing_hints,
        )
        self.pins[name] = port
        return port

    @abstractmethod
    def _register_pins(self) -> None:
        """Subclass hook to define pins after base initialization."""
