"""Semantic port: interface point with ownership and routing hints."""

from __future__ import annotations

from dataclasses import dataclass, field

from manim_engineering.core.enums import ConnectionState, PortDirection, SignalType


@dataclass
class Port:
    """Semantic interface on a node — not a visual anchor."""

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
