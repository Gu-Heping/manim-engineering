"""Semantic node in a circuit graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.core.enums import PortDirection, SignalType
from manim_engineering.core.exceptions import InvalidPortError
from manim_engineering.core.port import Port


@dataclass
class Node:
    """A named entity that owns ports in the topology."""

    id: str
    label: str = ""
    ports: dict[str, Port] = field(default_factory=dict)

    @property
    def pins(self) -> dict[str, Port]:
        """Backward-compatible view of ``ports``."""
        return self.ports

    def add_port(
        self,
        name: str,
        *,
        direction: PortDirection,
        signal_type: SignalType,
        routing_hints: tuple[str, ...] = (),
    ) -> Port:
        """Register a port on this node and return it."""
        if name in self.ports:
            raise InvalidPortError(f"duplicate port {self.id}.{name}")
        port = Port(
            name=name,
            owner_id=self.id,
            direction=direction,
            signal_type=signal_type,
            routing_hints=routing_hints,
        )
        self.ports[name] = port
        return port

    def add_pin(
        self,
        name: str,
        *,
        direction: PortDirection,
        signal_type: SignalType,
        routing_hints: tuple[str, ...] = (),
    ) -> Port:
        """Backward-compatible alias for :meth:`add_port`."""
        return self.add_port(
            name,
            direction=direction,
            signal_type=signal_type,
            routing_hints=routing_hints,
        )

    def get_port(self, name: str) -> Port:
        """Return a port by name."""
        try:
            return self.ports[name]
        except KeyError as exc:
            raise InvalidPortError(f"unknown port {self.id}.{name}") from exc

    def get_pin(self, name: str) -> Port:
        """Backward-compatible alias for :meth:`get_port`."""
        return self.get_port(name)
