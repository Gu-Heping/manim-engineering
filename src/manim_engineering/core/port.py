"""Semantic port: interface point with ownership and routing hints."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.core.enums import ConnectionState, PortDirection, SignalType


@dataclass
class Port:
    """Semantic interface on a node — not a visual anchor.

    **Identity contract:** ``owner_id`` and ``name`` must remain stable after the
    port is registered on a ``Node`` and especially after ``CircuitGraph.connect``.
    ``id`` is derived as ``{owner_id}.{name}``; ``Connection`` and graph queries
    compare live ``port.id`` values. Mutating ``owner_id`` or ``name`` after wiring
    breaks ``Connection.involves`` / ``other_port`` and is unsupported.
    """

    name: str
    owner_id: str
    direction: PortDirection
    signal_type: SignalType
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    routing_hints: tuple[str, ...] = field(default_factory=tuple)

    @property
    def id(self) -> str:
        """Stable identifier ``{owner_id}.{name}``."""
        return f"{self.owner_id}.{self.name}"


# Backward-compatible alias.
Pin = Port
