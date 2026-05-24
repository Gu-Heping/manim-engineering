"""Explicit connection between two ports."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.core.port import Port


@dataclass(frozen=True)
class Connection:
    """Undirected link between two ports in the topology."""

    id: str
    port_a: Port
    port_b: Port

    @property
    def pin_a(self) -> Port:
        """Backward-compatible alias for :attr:`port_a`."""
        return self.port_a

    @property
    def pin_b(self) -> Port:
        """Backward-compatible alias for :attr:`port_b`."""
        return self.port_b

    def involves(self, port: Port) -> bool:
        """Return True if ``port`` is an endpoint of this connection."""
        port_id = port.id
        return port_id == self.port_a.id or port_id == self.port_b.id

    def other_port(self, port: Port) -> Port:
        """Return the peer port for ``port``."""
        if port.id == self.port_a.id:
            return self.port_b
        if port.id == self.port_b.id:
            return self.port_a
        msg = f"port {port.id} is not part of connection {self.id}"
        raise ValueError(msg)

    def other_pin(self, port: Port) -> Port:
        """Backward-compatible alias for :meth:`other_port`."""
        return self.other_port(port)
