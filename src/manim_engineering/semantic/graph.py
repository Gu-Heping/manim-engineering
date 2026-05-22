"""Circuit graph: explicit topology connect/disconnect and queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from manim_engineering.semantic.connection import Connection
from manim_engineering.semantic.enums import ConnectionState, PinDirection
from manim_engineering.semantic.exceptions import (
    InvalidConnectionError,
    InvalidPinError,
    TopologyError,
)
from manim_engineering.semantic.node import Node
from manim_engineering.semantic.pin import Pin


def _pin_pair_key(pin_a: Pin, pin_b: Pin) -> tuple[str, str]:
    return tuple(sorted((pin_a.id, pin_b.id)))


def _directions_compatible(pin_a: Pin, pin_b: Pin) -> bool:
    """Return True when pin directions allow a connection."""
    pair = {pin_a.direction, pin_b.direction}
    if PinDirection.INOUT in pair:
        return True
    return pair == {PinDirection.OUT, PinDirection.IN}


@dataclass
class CircuitGraph:
    """Topology container: nodes, pins, and explicit connections."""

    _nodes: dict[str, Node] = field(default_factory=dict)
    _connections: dict[str, Connection] = field(default_factory=dict)
    _pin_index: dict[str, Pin] = field(default_factory=dict)
    _pair_index: dict[tuple[str, str], str] = field(default_factory=dict)

    @property
    def nodes(self) -> tuple[Node, ...]:
        """All nodes in deterministic insertion order."""
        return tuple(self._nodes[nid] for nid in sorted(self._nodes))

    @property
    def connections(self) -> tuple[Connection, ...]:
        """All connections in deterministic id order."""
        return tuple(self._connections[cid] for cid in sorted(self._connections))

    def add_node(self, node: Node) -> Node:
        """Register a node and index its pins."""
        if node.id in self._nodes:
            raise TopologyError(f"duplicate node id: {node.id}")
        self._nodes[node.id] = node
        for pin in node.pins.values():
            self._register_pin(pin)
        return node

    def get_node(self, node_id: str) -> Node:
        """Return a node by id."""
        try:
            return self._nodes[node_id]
        except KeyError as exc:
            raise TopologyError(f"unknown node: {node_id}") from exc

    def get_pin(self, node_id: str, pin_name: str) -> Pin:
        """Return a pin belonging to a registered node."""
        return self.get_node(node_id).get_pin(pin_name)

    def connect(self, pin_a: Pin, pin_b: Pin) -> Connection:
        """Create an explicit connection between two pins."""
        self._ensure_pins_registered(pin_a, pin_b)
        if pin_a.id == pin_b.id:
            raise InvalidConnectionError("cannot connect a pin to itself")
        if not _directions_compatible(pin_a, pin_b):
            raise InvalidConnectionError(
                f"incompatible directions: {pin_a.direction.value} ↔ {pin_b.direction.value}"
            )
        pair_key = _pin_pair_key(pin_a, pin_b)
        if pair_key in self._pair_index:
            raise InvalidConnectionError(f"pins already connected: {pair_key}")

        connection_id = f"conn-{uuid4().hex[:12]}"
        connection = Connection(id=connection_id, pin_a=pin_a, pin_b=pin_b)
        self._connections[connection_id] = connection
        self._pair_index[pair_key] = connection_id
        pin_a.connection_state = ConnectionState.CONNECTED
        pin_b.connection_state = ConnectionState.CONNECTED
        return connection

    def disconnect(self, connection: Connection) -> None:
        """Remove a connection and update pin states when no longer linked."""
        stored = self._connections.get(connection.id)
        if stored is None:
            raise InvalidConnectionError(f"unknown connection: {connection.id}")

        pair_key = _pin_pair_key(connection.pin_a, connection.pin_b)
        del self._connections[connection.id]
        del self._pair_index[pair_key]

        for pin in (connection.pin_a, connection.pin_b):
            if not self._pin_has_connection(pin):
                pin.connection_state = ConnectionState.DISCONNECTED

    def get_connections(self, pin: Pin) -> tuple[Connection, ...]:
        """Return all connections involving ``pin``, sorted by connection id."""
        return tuple(
            conn
            for conn in self.connections
            if conn.involves(pin)
        )

    def are_connected(self, pin_a: Pin, pin_b: Pin) -> bool:
        """Return True when an explicit connection exists between the pins."""
        return _pin_pair_key(pin_a, pin_b) in self._pair_index

    def neighbors(self, pin: Pin) -> tuple[Pin, ...]:
        """Return peer pins connected to ``pin``, sorted by pin id."""
        peers = [conn.other_pin(pin) for conn in self.get_connections(pin)]
        return tuple(sorted(peers, key=lambda p: p.id))

    def _register_pin(self, pin: Pin) -> None:
        if pin.id in self._pin_index and self._pin_index[pin.id] is not pin:
            raise InvalidPinError(f"pin id collision: {pin.id}")
        self._pin_index[pin.id] = pin

    def _ensure_pins_registered(self, pin_a: Pin, pin_b: Pin) -> None:
        for pin in (pin_a, pin_b):
            if pin.id not in self._pin_index:
                raise InvalidPinError(f"pin not in graph: {pin.id}")
            if self._pin_index[pin.id] is not pin:
                raise InvalidPinError(f"pin instance mismatch for {pin.id}")

    def _pin_has_connection(self, pin: Pin) -> bool:
        return any(conn.involves(pin) for conn in self.connections)
