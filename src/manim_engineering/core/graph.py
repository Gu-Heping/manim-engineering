"""Circuit graph: explicit topology connect/disconnect and queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from manim_engineering.core.connection import Connection
from manim_engineering.core.enums import ConnectionState, PortDirection
from manim_engineering.core.exceptions import (
    InvalidConnectionError,
    InvalidPortError,
    TopologyError,
)
from manim_engineering.core.node import Node
from manim_engineering.core.port import Port


def _port_pair_key(port_a: Port, port_b: Port) -> tuple[str, str]:
    return tuple(sorted((port_a.id, port_b.id)))


def _connection_id_for_ports(port_a: Port, port_b: Port) -> str:
    """Deterministic connection id from sorted port ids (replay-stable)."""
    a_id, b_id = sorted((port_a.id, port_b.id))
    return f"conn-{a_id}--{b_id}"


def _directions_compatible(port_a: Port, port_b: Port) -> bool:
    """Return True when port directions allow a connection."""
    pair = {port_a.direction, port_b.direction}
    if PortDirection.INOUT in pair:
        return True
    return pair == {PortDirection.OUT, PortDirection.IN}


@dataclass
class CircuitGraph:
    """Topology container: nodes, ports, and explicit connections."""

    _nodes: dict[str, Node] = field(default_factory=dict)
    _connections: dict[str, Connection] = field(default_factory=dict)
    _port_index: dict[str, Port] = field(default_factory=dict)
    _pair_index: dict[tuple[str, str], str] = field(default_factory=dict)

    @property
    def nodes(self) -> tuple[Node, ...]:
        """All nodes in deterministic insertion order."""
        return tuple(self._nodes[nid] for nid in sorted(self._nodes))

    @property
    def connections(self) -> tuple[Connection, ...]:
        """All connections in deterministic id order."""
        return tuple(self._connections[cid] for cid in sorted(self._connections))

    def add(self, element: Any) -> Node:
        """Register a circuit element (must provide ``to_node()``) and index its ports."""
        return self.add_node(element.to_node())

    def add_node(self, node: Node) -> Node:
        """Register a node and index its ports."""
        if node.id in self._nodes:
            raise TopologyError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node
        for port in node.ports.values():
            self._register_port(port)
        return node

    def get_node(self, node_id: str) -> Node:
        """Return a node by id."""
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise TopologyError(f"unknown node: {node_id}") from exc

    def get_port(self, node_id: str, port_name: str) -> Port:
        """Return a port belonging to a registered node."""
        return self.get_node(node_id).get_port(port_name)

    def get_pin(self, node_id: str, pin_name: str) -> Port:
        """Backward-compatible alias for :meth:`get_port`."""
        return self.get_port(node_id, pin_name)

    def connect(self, port_a: Port, port_b: Port) -> Connection:
        """Create an explicit connection between two ports."""
        self._ensure_ports_registered(port_a, port_b)
        if port_a.id == port_b.id:
            raise InvalidConnectionError("cannot connect a port to itself")
        if not _directions_compatible(port_a, port_b):
            raise InvalidConnectionError(
                f"incompatible directions: {port_a.direction.value} ↔ {port_b.direction.value}"
            )
        pair_key = _port_pair_key(port_a, port_b)
        if pair_key in self._pair_index:
            raise InvalidConnectionError(f"ports already connected: {pair_key}")

        connection_id = _connection_id_for_ports(port_a, port_b)
        connection = Connection(id=connection_id, port_a=port_a, port_b=port_b)
        self._connections[connection_id] = connection
        self._pair_index[pair_key] = connection_id
        port_a.connection_state = ConnectionState.CONNECTED
        port_b.connection_state = ConnectionState.CONNECTED
        return connection

    def disconnect(self, connection: Connection) -> None:
        """Remove a connection and update port states when no longer linked."""
        stored = self._connections.get(connection.id)
        if stored is None:
            raise InvalidConnectionError(f"unknown connection: {connection.id}")

        pair_key = _port_pair_key(connection.port_a, connection.port_b)
        del self._connections[connection.id]
        del self._pair_index[pair_key]

        for port in (connection.port_a, connection.port_b):
            if not self._port_has_connection(port):
                port.connection_state = ConnectionState.DISCONNECTED

    def get_connections(self, port: Port) -> tuple[Connection, ...]:
        """Return all connections involving ``port``, sorted by connection id."""
        return tuple(conn for conn in self.connections if conn.involves(port))

    def are_connected(self, port_a: Port, port_b: Port) -> bool:
        """Return True when an explicit connection exists between the ports."""
        return _port_pair_key(port_a, port_b) in self._pair_index

    def neighbors(self, port: Port) -> tuple[Port, ...]:
        """Return peer ports connected to ``port``, sorted by port id."""
        peers = [conn.other_port(port) for conn in self.get_connections(port)]
        return tuple(sorted(peers, key=lambda p: p.id))

    def _register_port(self, port: Port) -> None:
        if port.id in self._port_index and self._port_index[port.id] is not port:
            raise InvalidPortError(f"port id collision: {port.id}")
        self._port_index[port.id] = port

    def _ensure_ports_registered(self, port_a: Port, port_b: Port) -> None:
        for port in (port_a, port_b):
            if port.id not in self._port_index:
                raise InvalidPortError(f"port not in graph: {port.id}")
            if self._port_index[port.id] is not port:
                raise InvalidPortError(f"port instance mismatch for {port.id}")

    def _port_has_connection(self, port: Port) -> bool:
        return any(conn.involves(port) for conn in self.connections)
