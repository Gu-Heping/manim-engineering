"""Electrical net grouping and hub-based orthogonal routing."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.connection import Connection
from manim_engineering.layout.routing import (
    ensure_visible_connection,
    merge_routing_hints,
    points_to_segments,
    route_orthogonal,
    route_through_waypoints,
    sibling_pins_to_avoid,
)
from manim_engineering.layout.types import ComponentPlacement, Point2D, Segment, WirePath

_COORD_EPS = 1e-6


@dataclass(frozen=True)
class ElectricalNet:
    """Pins linked by explicit graph connections (equipotential group)."""

    net_id: str
    pin_ids: frozenset[str]
    connection_ids: frozenset[str]


def net_id_for_pins(pin_ids: frozenset[str]) -> str:
    """Deterministic net label from sorted port ids."""
    return "net-" + "--".join(sorted(pin_ids))


class _UnionFind:
    def __init__(self, items: Sequence[str]) -> None:
        self._parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self._parent[item]
        if parent != item:
            self._parent[item] = self.find(parent)
        return self._parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self._parent[root_right] = root_left


def group_connections_into_nets(connections: Sequence[Connection]) -> tuple[ElectricalNet, ...]:
    """Union-find group connections into equipotential nets."""
    if not connections:
        return ()

    pin_ids = sorted(
        {connection.port_a.id for connection in connections}
        | {connection.port_b.id for connection in connections}
    )
    uf = _UnionFind(pin_ids)

    for connection in connections:
        uf.union(connection.port_a.id, connection.port_b.id)

    groups: dict[str, set[str]] = {}
    conn_by_group: dict[str, set[str]] = {}
    for connection in connections:
        root = uf.find(connection.port_a.id)
        groups.setdefault(root, set()).add(connection.port_a.id)
        groups[root].add(connection.port_b.id)
        conn_by_group.setdefault(root, set()).add(connection.id)

    nets: list[ElectricalNet] = []
    for root in sorted(groups):
        pins = frozenset(groups[root])
        nets.append(
            ElectricalNet(
                net_id=net_id_for_pins(pins),
                pin_ids=pins,
                connection_ids=frozenset(conn_by_group[root]),
            )
        )
    return tuple(nets)


def _points_close(left: Point2D, right: Point2D) -> bool:
    return abs(left.x - right.x) <= _COORD_EPS and abs(left.y - right.y) <= _COORD_EPS


def _segment_key(segment: Segment) -> tuple[float, float, float, float]:
    a = (round(segment.start.x, 6), round(segment.start.y, 6))
    b = (round(segment.end.x, 6), round(segment.end.y, 6))
    return (*a, *b) if a <= b else (*b, *a)


def _dedupe_points(points: list[Point2D]) -> tuple[Point2D, ...]:
    if not points:
        return ()
    out = [points[0]]
    for point in points[1:]:
        if not _points_close(point, out[-1]):
            out.append(point)
    return tuple(out)


def _route_hub_to_pin(
    hub: Point2D,
    pin: Point2D,
    *,
    hints: tuple[str, ...],
    avoid_points: tuple[Point2D, ...],
) -> tuple[Point2D, ...]:
    """Orthogonal path from hub to pin with stub-first preference on horizontal pins."""
    if _points_close(hub, pin):
        return (hub,)

    if abs(hub.y - pin.y) <= _COORD_EPS:
        return route_orthogonal(hub, pin, hints=hints, avoid_points=avoid_points)

    if abs(hub.x - pin.x) <= _COORD_EPS:
        return route_orthogonal(hub, pin, hints=hints, avoid_points=avoid_points)

    hint_set = {hint.lower() for hint in hints}
    if "horizontal" in hint_set and pin.x > hub.x + _COORD_EPS:
        stub = Point2D(hub.x, pin.y)
        return _dedupe_points([hub, stub, pin])

    if pin.y >= hub.y:
        corner = Point2D(hub.x, pin.y)
        return _dedupe_points([hub, corner, pin])

    return route_orthogonal(hub, pin, hints=hints, avoid_points=avoid_points)


def _hints_for_pin_in_net(
    pin_id: str,
    net: ElectricalNet,
    connections_by_id: Mapping[str, Connection],
) -> tuple[str, ...]:
    for connection_id in sorted(net.connection_ids):
        connection = connections_by_id[connection_id]
        if connection.port_a.id == pin_id or connection.port_b.id == pin_id:
            return merge_routing_hints(
                connection.port_a.routing_hints,
                connection.port_b.routing_hints,
            )
    return ()


def _route_star_net(
    net: ElectricalNet,
    hub: Point2D,
    pin_positions: Mapping[str, Point2D],
    elements: Mapping[str, CircuitElement],
    connections_by_id: Mapping[str, Connection],
    placements_by_id: Mapping[str, ComponentPlacement],
) -> list[WirePath]:
    """Hub-and-spoke routes for a multi-pin net; de-duplicates shared trunk segments."""
    seen_segments: set[tuple[float, float, float, float]] = set()
    wires: list[WirePath] = []

    for pin_id in sorted(net.pin_ids):
        pin_point = pin_positions[pin_id]
        hints = _hints_for_pin_in_net(pin_id, net, connections_by_id)
        connection = next(
            connections_by_id[cid]
            for cid in sorted(net.connection_ids)
            if pin_id in (connections_by_id[cid].port_a.id, connections_by_id[cid].port_b.id)
        )
        avoid_points = sibling_pins_to_avoid(
            connection,
            pin_positions,
            elements,
        )

        if _points_close(pin_point, hub):
            points = ensure_visible_connection(
                (hub,),
                connection=connection,
                pin_positions=pin_positions,
                placements_by_id=placements_by_id,
                hints=hints,
            )
            segments = points_to_segments(points)
            branch_segments = [
                segment for segment in segments if _segment_key(segment) not in seen_segments
            ]
            for segment in branch_segments:
                seen_segments.add(_segment_key(segment))
            if branch_segments:
                wires.append(
                    WirePath(
                        connection_id=f"{net.net_id}/{pin_id}",
                        points=_segments_to_points(branch_segments),
                        segments=tuple(branch_segments),
                    )
                )
            continue

        points = _route_hub_to_pin(
            hub,
            pin_point,
            hints=hints,
            avoid_points=avoid_points,
        )
        segments = points_to_segments(points)
        branch_segments = [
            segment for segment in segments if _segment_key(segment) not in seen_segments
        ]
        for segment in branch_segments:
            seen_segments.add(_segment_key(segment))

        if not branch_segments:
            continue

        branch_points = _segments_to_points(branch_segments)
        wires.append(
            WirePath(
                connection_id=f"{net.net_id}/{pin_id}",
                points=branch_points,
                segments=tuple(branch_segments),
            )
        )

    return wires


def _segments_to_points(segments: Sequence[Segment]) -> tuple[Point2D, ...]:
    if not segments:
        return ()
    points: list[Point2D] = [segments[0].start]
    for segment in segments:
        points.append(segment.end)
    return _dedupe_points(points)


def _connection_on_same_element(connection: Connection) -> bool:
    """True when both ports belong to one component (e.g. bulk tied to source)."""
    return connection.port_a.owner_id == connection.port_b.owner_id


def _route_connection(
    connection: Connection,
    pin_positions: Mapping[str, Point2D],
    elements: Mapping[str, CircuitElement],
    placements_by_id: Mapping[str, ComponentPlacement],
    *,
    waypoints: Sequence[Point2D] = (),
) -> WirePath:
    start = pin_positions[connection.port_a.id]
    end = pin_positions[connection.port_b.id]
    hints = merge_routing_hints(
        connection.port_a.routing_hints,
        connection.port_b.routing_hints,
    )
    avoid_points = sibling_pins_to_avoid(connection, pin_positions, elements)
    if waypoints:
        points = route_through_waypoints(
            start,
            end,
            waypoints,
            hints=hints,
            avoid_points=avoid_points,
        )
    else:
        points = route_orthogonal(start, end, hints=hints, avoid_points=avoid_points)
    points = ensure_visible_connection(
        points,
        connection=connection,
        pin_positions=pin_positions,
        placements_by_id=placements_by_id,
        hints=hints,
    )
    return WirePath(
        connection_id=connection.id,
        points=points,
        segments=points_to_segments(points),
    )


def connection_for_wire(
    wire: WirePath,
    connections_by_id: Mapping[str, Connection],
) -> Connection:
    """Resolve graph connection metadata for a routed wire (including net branches)."""
    connection_id = wire.connection_id
    if connection_id in connections_by_id:
        return connections_by_id[connection_id]

    if "/" in connection_id:
        _net_label, pin_id = connection_id.rsplit("/", 1)
        for connection in connections_by_id.values():
            if pin_id in (connection.port_a.id, connection.port_b.id):
                return connection

    msg = f"no connection for wire {connection_id!r}"
    raise KeyError(msg)


def collect_junction_nodes(
    connections: Sequence[Connection],
    pin_positions: Mapping[str, Point2D],
    *,
    net_waypoints: Mapping[str, Point2D] | None = None,
) -> frozenset[Point2D]:
    """Electrical junction coordinates: net hubs and 2+ pins sharing a location."""
    waypoints = net_waypoints or {}
    keys: set[tuple[float, float]] = set()

    for net in group_connections_into_nets(connections):
        hub = waypoints.get(net.net_id)
        if hub is not None and len(net.pin_ids) >= 3:
            keys.add((round(hub.x, 6), round(hub.y, 6)))

        grouped: dict[tuple[float, float], int] = {}
        for pin_id in net.pin_ids:
            point = pin_positions[pin_id]
            key = (round(point.x, 6), round(point.y, 6))
            grouped[key] = grouped.get(key, 0) + 1
        for key, count in grouped.items():
            if count >= 2:
                keys.add(key)

    return frozenset(Point2D(x, y) for x, y in keys)


def route_nets(
    connections: Sequence[Connection],
    pin_positions: Mapping[str, Point2D],
    elements: Mapping[str, CircuitElement],
    *,
    net_waypoints: Mapping[str, Point2D] | None = None,
    connection_waypoints: Mapping[str, Sequence[Point2D]] | None = None,
    placements: Sequence[ComponentPlacement] = (),
) -> tuple[WirePath, ...]:
    """Route all connections, using hub routing for multi-pin nets with waypoints."""
    if not connections:
        return ()

    connections_by_id = {connection.id: connection for connection in connections}
    waypoints = net_waypoints or {}
    conn_waypoints = connection_waypoints or {}
    placements_by_id = {placement.element_id: placement for placement in placements}
    nets = group_connections_into_nets(connections)
    routed: list[WirePath] = []

    for net in nets:
        hub = waypoints.get(net.net_id)
        if hub is not None and len(net.pin_ids) >= 3:
            routed.extend(
                _route_star_net(
                    net,
                    hub,
                    pin_positions,
                    elements,
                    connections_by_id,
                    placements_by_id,
                )
            )
            continue

        for connection_id in sorted(net.connection_ids):
            connection = connections_by_id[connection_id]
            if _connection_on_same_element(connection):
                continue
            routed.append(
                _route_connection(
                    connection,
                    pin_positions,
                    elements,
                    placements_by_id,
                    waypoints=conn_waypoints.get(connection_id, ()),
                )
            )

    return tuple(routed)
