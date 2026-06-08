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
    segments_intersect,
    sibling_pins_to_avoid,
)
from manim_engineering.layout.types import (
    ComponentPlacement,
    LayoutBBox,
    Point2D,
    RoutingIssue,
    RoutingIssueSeverity,
    RoutingReport,
    Segment,
    WirePath,
)

_COORD_EPS = 1e-6
WIRE_TRACK_SPACING = 0.15
_MAX_TRACK_SPACING_PASSES = 4
_MAX_DETOUR_PASSES = 4
_DETOUR_MARGIN = 0.04
_SEVERITY_RANK: dict[RoutingIssueSeverity, int] = {
    "cosmetic": 0,
    "ambiguous": 1,
    "blocking": 2,
}


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


def _segment_axis(segment: Segment) -> str:
    return "vertical" if abs(segment.start.x - segment.end.x) <= _COORD_EPS else "horizontal"


def _overlap_length(left: Segment, right: Segment) -> float:
    if _segment_axis(left) != _segment_axis(right):
        return 0.0
    if _segment_axis(left) == "vertical":
        if abs(left.start.x - right.start.x) > _COORD_EPS:
            return 0.0
        lo_a, hi_a = sorted((left.start.y, left.end.y))
        lo_b, hi_b = sorted((right.start.y, right.end.y))
    else:
        if abs(left.start.y - right.start.y) > _COORD_EPS:
            return 0.0
        lo_a, hi_a = sorted((left.start.x, left.end.x))
        lo_b, hi_b = sorted((right.start.x, right.end.x))
    return max(0.0, min(hi_a, hi_b) - max(lo_a, lo_b))


def _crossing_point(left: Segment, right: Segment) -> Point2D | None:
    if _segment_axis(left) == _segment_axis(right):
        return None
    vertical = left if _segment_axis(left) == "vertical" else right
    horizontal = right if vertical is left else left
    return Point2D(vertical.start.x, horizontal.start.y)


def _placement_bbox(placement: ComponentPlacement) -> LayoutBBox:
    return LayoutBBox(
        min_x=placement.origin.x,
        min_y=placement.origin.y,
        max_x=placement.origin.x + placement.bounds.width,
        max_y=placement.origin.y + placement.bounds.height,
    )


def _segment_passes_through_bbox(segment: Segment, bbox: LayoutBBox) -> bool:
    if _segment_axis(segment) == "horizontal":
        y = segment.start.y
        if y <= bbox.min_y + _COORD_EPS or y >= bbox.max_y - _COORD_EPS:
            return False
        left = min(segment.start.x, segment.end.x)
        right = max(segment.start.x, segment.end.x)
        return left < bbox.max_x - _COORD_EPS and right > bbox.min_x + _COORD_EPS

    x = segment.start.x
    if x <= bbox.min_x + _COORD_EPS or x >= bbox.max_x - _COORD_EPS:
        return False
    low = min(segment.start.y, segment.end.y)
    high = max(segment.start.y, segment.end.y)
    return low < bbox.max_y - _COORD_EPS and high > bbox.min_y + _COORD_EPS


_PIN_PROXIMITY_X = 0.08
_PIN_PROXIMITY_Y = 0.08


def _segment_near_pin(segment: Segment, pin: Point2D) -> bool:
    if _segment_axis(segment) == "horizontal":
        y = segment.start.y
        if abs(y - pin.y) > _PIN_PROXIMITY_Y:
            return False
        left = min(segment.start.x, segment.end.x)
        right = max(segment.start.x, segment.end.x)
        return left <= pin.x + _PIN_PROXIMITY_X and right >= pin.x - _PIN_PROXIMITY_X

    x = segment.start.x
    if abs(x - pin.x) > _PIN_PROXIMITY_X:
        return False
    low = min(segment.start.y, segment.end.y)
    high = max(segment.start.y, segment.end.y)
    return low <= pin.y + _PIN_PROXIMITY_Y and high >= pin.y - _PIN_PROXIMITY_Y


def _wire_owner_ids(
    wire: WirePath,
    connections_by_id: Mapping[str, Connection],
) -> frozenset[str]:
    connection = connection_for_wire(wire, connections_by_id)
    return frozenset({connection.port_a.owner_id, connection.port_b.owner_id})


def _wire_connected_pin_ids(
    wire: WirePath,
    connections_by_id: Mapping[str, Connection],
) -> frozenset[str]:
    connection = connection_for_wire(wire, connections_by_id)
    return frozenset({connection.port_a.id, connection.port_b.id})


def _wire_connected_pin_points(
    wire: WirePath,
    *,
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
) -> frozenset[Point2D]:
    points = {
        pin_positions[pin_id]
        for pin_id in _wire_connected_pin_ids(wire, connections_by_id)
        if pin_id in pin_positions
    }
    return frozenset(points)


def _wire_net_branch_pin_ids(wire: WirePath) -> frozenset[str]:
    connection_id = wire.connection_id
    if not _is_synthetic_net_branch_id(connection_id):
        return frozenset()
    net_label, _pin_id = connection_id.rsplit("/", 1)
    encoded = net_label[len("net-") :]
    if not encoded:
        return frozenset()
    return frozenset(part for part in encoded.split("--") if part)


def _is_synthetic_net_branch_id(connection_id: str) -> bool:
    return connection_id.startswith("net-") and "/" in connection_id


def _pin_owner_id(pin_id: str) -> str:
    return pin_id.rsplit(".", 1)[0] if "." in pin_id else pin_id


def _wire_net_branch_owner_ids(wire: WirePath) -> frozenset[str]:
    return frozenset(_pin_owner_id(pin_id) for pin_id in _wire_net_branch_pin_ids(wire))


def _routing_issue_severity(kind: str) -> RoutingIssueSeverity:
    if kind in {"parallel_overlap", "shared_segment"}:
        return "cosmetic"
    if kind in {"crossing_without_junction", "wire_near_unconnected_pin"}:
        return "ambiguous"
    return "blocking"


def _same_net_branch_family(left: WirePath, right: WirePath) -> bool:
    if not left.connection_id.startswith("net-") or not right.connection_id.startswith("net-"):
        return False
    if "/" not in left.connection_id or "/" not in right.connection_id:
        return False
    return left.connection_id.rsplit("/", 1)[0] == right.connection_id.rsplit("/", 1)[0]


def _track_offsets(count: int) -> tuple[int, ...]:
    if count <= 0:
        return ()
    offsets = [0]
    step = 1
    while len(offsets) < count:
        offsets.append(step)
        if len(offsets) < count:
            offsets.append(-step)
        step += 1
    return tuple(offsets)


def _dedupe_points(points: list[Point2D]) -> tuple[Point2D, ...]:
    if not points:
        return ()
    out = [points[0]]
    for point in points[1:]:
        if not _points_close(point, out[-1]):
            out.append(point)
    return tuple(out)


def _wire_has_zero_length_segment(wire: WirePath) -> bool:
    return any(_points_close(segment.start, segment.end) for segment in wire.segments)


def _replace_segment_in_wire(
    wire: WirePath,
    *,
    segment_index: int,
    replacement_points: Sequence[Point2D],
) -> WirePath:
    if segment_index < 0 or segment_index >= len(wire.segments):
        return wire

    points = list(wire.points)
    rebuilt = points[:segment_index]
    rebuilt.extend(replacement_points)
    rebuilt.extend(points[segment_index + 2 :])
    deduped = _dedupe_points(rebuilt)
    return WirePath(
        connection_id=wire.connection_id,
        points=deduped,
        segments=points_to_segments(deduped),
    )


def _can_rewrite_segment_for_detour(
    wire: WirePath,
    *,
    segment_index: int,
) -> bool:
    if len(wire.segments) == 1:
        return True
    if len(wire.segments) == 2:
        return True
    return 0 < segment_index < len(wire.segments) - 1


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


def _segment_hits_foreign_bbox(
    segment: Segment,
    *,
    placements: Sequence[ComponentPlacement],
    owner_ids: frozenset[str],
) -> ComponentPlacement | None:
    for placement in placements:
        if placement.element_id in owner_ids:
            continue
        bbox = _placement_bbox(placement)
        if _segment_passes_through_bbox(segment, bbox):
            return placement
    return None


def _segment_foreign_bboxes(
    segment: Segment,
    *,
    placements: Sequence[ComponentPlacement],
    owner_ids: frozenset[str],
) -> tuple[ComponentPlacement, ...]:
    hits: list[ComponentPlacement] = []
    for placement in placements:
        if placement.element_id in owner_ids:
            continue
        bbox = _placement_bbox(placement)
        if _segment_passes_through_bbox(segment, bbox):
            hits.append(placement)
    return tuple(hits)


def _segment_hits_unconnected_pin(
    segment: Segment,
    *,
    pin_positions: Mapping[str, Point2D],
    connected_pin_ids: frozenset[str],
    connected_pin_points: frozenset[Point2D],
    junction_keys: frozenset[tuple[float, float]],
) -> tuple[str, Point2D] | None:
    for pin_id, pin_point in pin_positions.items():
        if pin_id in connected_pin_ids or pin_point in connected_pin_points:
            continue
        if (round(pin_point.x, 6), round(pin_point.y, 6)) in junction_keys:
            continue
        if _segment_near_pin(segment, pin_point):
            return pin_id, pin_point
    return None


def _segment_unconnected_pin_hits(
    segment: Segment,
    *,
    pin_positions: Mapping[str, Point2D],
    connected_pin_ids: frozenset[str],
    connected_pin_points: frozenset[Point2D],
    junction_keys: frozenset[tuple[float, float]],
) -> tuple[tuple[str, Point2D], ...]:
    hits: list[tuple[str, Point2D]] = []
    for pin_id, pin_point in pin_positions.items():
        if pin_id in connected_pin_ids or pin_point in connected_pin_points:
            continue
        if (round(pin_point.x, 6), round(pin_point.y, 6)) in junction_keys:
            continue
        if _segment_near_pin(segment, pin_point):
            hits.append((pin_id, pin_point))
    return tuple(hits)


def _wire_is_safe_for_context(
    wire: WirePath,
    *,
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> bool:
    owner_ids = _wire_owner_ids(wire, connections_by_id)
    connected_pin_ids = _wire_connected_pin_ids(wire, connections_by_id)
    connected_pin_points = _wire_connected_pin_points(
        wire,
        pin_positions=pin_positions,
        connections_by_id=connections_by_id,
    )
    junction_keys = frozenset((round(node.x, 6), round(node.y, 6)) for node in junction_nodes)

    if _wire_has_zero_length_segment(wire):
        return False

    for segment in wire.segments:
        if (
            _segment_hits_foreign_bbox(
                segment,
                placements=placements,
                owner_ids=owner_ids,
            )
            is not None
        ):
            return False
        if _segment_hits_unconnected_pin(
            segment,
            pin_positions=pin_positions,
            connected_pin_ids=connected_pin_ids,
            connected_pin_points=connected_pin_points,
            junction_keys=junction_keys,
        ) is not None:
            return False
    return True


def _pin_detour_offsets() -> tuple[int, ...]:
    return (1, -1, 2, -2)


def _pin_detour_step(segment: Segment) -> float:
    if _segment_axis(segment) == "horizontal":
        return max(WIRE_TRACK_SPACING, _PIN_PROXIMITY_Y + _DETOUR_MARGIN)
    return max(WIRE_TRACK_SPACING, _PIN_PROXIMITY_X + _DETOUR_MARGIN)


def _replace_segment_with_parallel_dogleg(
    wire: WirePath,
    *,
    segment_index: int,
    shifted_coordinate: float,
) -> WirePath:
    segment = wire.segments[segment_index]
    start = wire.points[segment_index]
    end = wire.points[segment_index + 1]
    if _segment_axis(segment) == "horizontal":
        replacement = (
            start,
            Point2D(start.x, shifted_coordinate),
            Point2D(end.x, shifted_coordinate),
            end,
        )
    else:
        replacement = (
            start,
            Point2D(shifted_coordinate, start.y),
            Point2D(shifted_coordinate, end.y),
            end,
        )
    return _replace_segment_in_wire(
        wire,
        segment_index=segment_index,
        replacement_points=replacement,
    )


def _replace_corner_in_wire(
    wire: WirePath,
    *,
    segment_index: int,
    alternate_corner: Point2D,
) -> WirePath:
    points = list(wire.points)
    if segment_index < 0 or segment_index + 2 >= len(points):
        return wire
    rebuilt = points[:segment_index]
    rebuilt.extend((points[segment_index], alternate_corner, points[segment_index + 2]))
    rebuilt.extend(points[segment_index + 3 :])
    deduped = _dedupe_points(rebuilt)
    return WirePath(
        connection_id=wire.connection_id,
        points=deduped,
        segments=points_to_segments(deduped),
    )


def _can_rewrite_segment_for_shared_split(
    wire: WirePath,
    *,
    segment_index: int,
) -> bool:
    if len(wire.segments) == 1:
        return True
    if len(wire.segments) == 2:
        return True
    return 0 <= segment_index < len(wire.segments)


def _try_detour_near_pin(
    wire: WirePath,
    *,
    segment_index: int,
    pin_points: Sequence[Point2D],
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> WirePath | None:
    if not _can_rewrite_segment_for_detour(wire, segment_index=segment_index):
        return None

    segment = wire.segments[segment_index]
    step = _pin_detour_step(segment)
    shifted_candidates: list[float] = []
    for multiplier in _pin_detour_offsets():
        for pin_point in pin_points:
            if _segment_axis(segment) == "horizontal":
                shifted_coordinate = pin_point.y + multiplier * step
            else:
                shifted_coordinate = pin_point.x + multiplier * step
            if shifted_coordinate not in shifted_candidates:
                shifted_candidates.append(shifted_coordinate)
    for shifted_coordinate in shifted_candidates:
        candidate = _replace_segment_with_parallel_dogleg(
            wire,
            segment_index=segment_index,
            shifted_coordinate=shifted_coordinate,
        )
        if candidate == wire:
            continue
        if candidate.points[0] != wire.points[0] or candidate.points[-1] != wire.points[-1]:
            continue
        if _wire_is_safe_for_context(
            candidate,
            placements=placements,
            pin_positions=pin_positions,
            connections_by_id=connections_by_id,
            junction_nodes=junction_nodes,
        ):
            return candidate
    return None


def _try_detour_through_component(
    wire: WirePath,
    *,
    segment_index: int,
    obstacles: Sequence[ComponentPlacement],
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> WirePath | None:
    if not _can_rewrite_segment_for_detour(wire, segment_index=segment_index):
        return None

    segment = wire.segments[segment_index]
    candidates: list[float] = []
    for obstacle in obstacles:
        bbox = _placement_bbox(obstacle)
        if _segment_axis(segment) == "horizontal":
            shifted_options = (bbox.max_y + _DETOUR_MARGIN, bbox.min_y - _DETOUR_MARGIN)
        else:
            shifted_options = (bbox.max_x + _DETOUR_MARGIN, bbox.min_x - _DETOUR_MARGIN)
        for shifted_coordinate in shifted_options:
            if shifted_coordinate not in candidates:
                candidates.append(shifted_coordinate)

    for shifted_coordinate in candidates:
        candidate = _replace_segment_with_parallel_dogleg(
            wire,
            segment_index=segment_index,
            shifted_coordinate=shifted_coordinate,
        )
        if candidate == wire:
            continue
        if candidate.points[0] != wire.points[0] or candidate.points[-1] != wire.points[-1]:
            continue
        if _wire_is_safe_for_context(
            candidate,
            placements=placements,
            pin_positions=pin_positions,
            connections_by_id=connections_by_id,
            junction_nodes=junction_nodes,
        ):
            return candidate
    return None


def _try_detour_via_alternate_l_path(
    wire: WirePath,
    *,
    segment_index: int = 0,
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> WirePath | None:
    if segment_index < 0 or segment_index + 1 >= len(wire.segments):
        return None

    first = wire.segments[segment_index]
    second = wire.segments[segment_index + 1]
    if _segment_axis(first) == _segment_axis(second):
        return None

    start = wire.points[segment_index]
    end = wire.points[segment_index + 2]
    if _segment_axis(first) == "horizontal":
        alt_corner = Point2D(start.x, end.y)
    else:
        alt_corner = Point2D(end.x, start.y)

    candidate = _replace_corner_in_wire(
        wire,
        segment_index=segment_index,
        alternate_corner=alt_corner,
    )
    if candidate == wire:
        return None
    if _wire_is_safe_for_context(
        candidate,
        placements=placements,
        pin_positions=pin_positions,
        connections_by_id=connections_by_id,
        junction_nodes=junction_nodes,
    ):
        return candidate
    return None


def _detour_wire_once(
    wire: WirePath,
    *,
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> WirePath:
    if _is_synthetic_net_branch_id(wire.connection_id):
        # Canonical hub/spoke branches intentionally keep their generated geometry.
        # Local doglegs on those synthetic branches can easily fight the shared
        # backbone semantics, so this pass leaves them untouched and surfaces any
        # residual hazards through routing diagnostics instead.
        return wire

    owner_ids = _wire_owner_ids(wire, connections_by_id)
    connected_pin_ids = _wire_connected_pin_ids(wire, connections_by_id)
    connected_pin_points = _wire_connected_pin_points(
        wire,
        pin_positions=pin_positions,
        connections_by_id=connections_by_id,
    )
    junction_keys = frozenset((round(node.x, 6), round(node.y, 6)) for node in junction_nodes)
    saw_hazard = False
    hazard_segment_indices: set[int] = set()

    for segment_index, segment in enumerate(wire.segments):
        obstacles = _segment_foreign_bboxes(
            segment,
            placements=placements,
            owner_ids=owner_ids,
        )
        if obstacles:
            saw_hazard = True
            hazard_segment_indices.add(segment_index)
            candidate = _try_detour_through_component(
                wire,
                segment_index=segment_index,
                obstacles=obstacles,
                placements=placements,
                pin_positions=pin_positions,
                connections_by_id=connections_by_id,
                junction_nodes=junction_nodes,
            )
            if candidate is not None:
                return candidate

        pin_hits = _segment_unconnected_pin_hits(
            segment,
            pin_positions=pin_positions,
            connected_pin_ids=connected_pin_ids,
            connected_pin_points=connected_pin_points,
            junction_keys=junction_keys,
        )
        if pin_hits:
            saw_hazard = True
            hazard_segment_indices.add(segment_index)
            candidate = _try_detour_near_pin(
                wire,
                segment_index=segment_index,
                pin_points=tuple(point for _pin_id, point in pin_hits),
                placements=placements,
                pin_positions=pin_positions,
                connections_by_id=connections_by_id,
                junction_nodes=junction_nodes,
            )
            if candidate is not None:
                return candidate

    if saw_hazard:
        pair_indices: set[int] = set()
        for segment_index in hazard_segment_indices:
            if segment_index > 0:
                pair_indices.add(segment_index - 1)
            if segment_index < len(wire.segments) - 1:
                pair_indices.add(segment_index)
        for pair_index in sorted(pair_indices):
            candidate = _try_detour_via_alternate_l_path(
                wire,
                segment_index=pair_index,
                placements=placements,
                pin_positions=pin_positions,
                connections_by_id=connections_by_id,
                junction_nodes=junction_nodes,
            )
            if candidate is not None:
                return candidate

    return wire


def apply_wire_detours(
    wires: Sequence[WirePath],
    *,
    placements: Sequence[ComponentPlacement],
    pin_positions: Mapping[str, Point2D],
    connections_by_id: Mapping[str, Connection],
    junction_nodes: frozenset[Point2D],
) -> tuple[tuple[WirePath, ...], int]:
    """Apply small deterministic dogleg detours around unrelated pins and bodies."""

    current = tuple(wires)
    changed_ids: set[str] = set()

    for _pass in range(_MAX_DETOUR_PASSES):
        changed_this_pass = False
        updated: list[WirePath] = []
        for wire in current:
            rewritten = _detour_wire_once(
                wire,
                placements=placements,
                pin_positions=pin_positions,
                connections_by_id=connections_by_id,
                junction_nodes=junction_nodes,
            )
            if rewritten != wire:
                changed_ids.add(wire.connection_id)
                changed_this_pass = True
                updated.append(rewritten)
            else:
                updated.append(wire)
        current = tuple(updated)
        if not changed_this_pass:
            break
    return current, len(changed_ids)


def _overlap_components(
    wire_segments: Sequence[tuple[str, Segment]],
) -> tuple[tuple[tuple[str, Segment], ...], ...]:
    if not wire_segments:
        return ()

    adjacency: dict[int, set[int]] = {index: set() for index in range(len(wire_segments))}
    for left_index, (_left_id, left_segment) in enumerate(wire_segments):
        for right_index in range(left_index + 1, len(wire_segments)):
            _right_id, right_segment = wire_segments[right_index]
            if _overlap_length(left_segment, right_segment) > _COORD_EPS:
                adjacency[left_index].add(right_index)
                adjacency[right_index].add(left_index)

    components: list[tuple[tuple[str, Segment], ...]] = []
    seen: set[int] = set()
    for index in range(len(wire_segments)):
        if index in seen or not adjacency[index]:
            continue
        stack = [index]
        component_indices: list[int] = []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            component_indices.append(current)
            stack.extend(adjacency[current] - seen)
        components.append(tuple(wire_segments[i] for i in sorted(component_indices)))
    return tuple(components)


def _exact_shared_components(
    wire_segments: Sequence[tuple[str, int, Segment]],
) -> tuple[tuple[tuple[str, int, Segment], ...], ...]:
    groups: dict[tuple[float, float, float, float], list[tuple[str, int, Segment]]] = {}
    for connection_id, segment_index, segment in wire_segments:
        groups.setdefault(_segment_key(segment), []).append((connection_id, segment_index, segment))
    return tuple(
        tuple(sorted(items, key=lambda item: (item[0], item[1])))
        for items in groups.values()
        if len(items) >= 2
    )


def _apply_shared_segment_split_pass(
    wires: Sequence[WirePath],
    *,
    placements: Sequence[ComponentPlacement] = (),
    pin_positions: Mapping[str, Point2D] | None = None,
    connections_by_id: Mapping[str, Connection] | None = None,
    junction_nodes: frozenset[Point2D] = frozenset(),
) -> tuple[tuple[WirePath, ...], int]:
    """Split exact shared segments before generic overlap spacing."""

    wire_by_id = {wire.connection_id: wire for wire in wires}
    updated: dict[str, WirePath] = {}
    shifted_count = 0

    horizontal_groups: dict[float, list[tuple[str, int, Segment]]] = {}
    vertical_groups: dict[float, list[tuple[str, int, Segment]]] = {}
    for wire in wires:
        for segment_index, segment in enumerate(wire.segments):
            if _segment_axis(segment) == "horizontal":
                horizontal_groups.setdefault(round(segment.start.y, 6), []).append(
                    (wire.connection_id, segment_index, segment)
                )
            else:
                vertical_groups.setdefault(round(segment.start.x, 6), []).append(
                    (wire.connection_id, segment_index, segment)
                )

    for groups in (horizontal_groups, vertical_groups):
        for wire_segments in groups.values():
            components = _exact_shared_components(tuple(wire_segments))
            for component in components:
                ordered = sorted(component, key=lambda item: item[0])
                for offset_index, (connection_id, original_index, original_segment) in zip(
                    _track_offsets(len(ordered)),
                    ordered,
                ):
                    if offset_index == 0:
                        continue
                    current_wire = updated.get(connection_id, wire_by_id[connection_id])
                    segment_index = _find_segment_index(current_wire, original_segment)
                    if segment_index is None:
                        segment_index = (
                            original_index
                            if original_index < len(current_wire.segments)
                            else None
                        )
                    if segment_index is None:
                        continue
                    if not _can_rewrite_segment_for_shared_split(
                        current_wire,
                        segment_index=segment_index,
                    ):
                        continue
                    current_segment = current_wire.segments[segment_index]
                    if _segment_axis(current_segment) == "horizontal":
                        shifted_coordinate = (
                            current_segment.start.y + offset_index * WIRE_TRACK_SPACING
                        )
                    else:
                        shifted_coordinate = (
                            current_segment.start.x + offset_index * WIRE_TRACK_SPACING
                        )
                    shifted = _replace_segment_with_parallel_dogleg(
                        current_wire,
                        segment_index=segment_index,
                        shifted_coordinate=shifted_coordinate,
                    )
                    if shifted == current_wire:
                        continue
                    if (
                        placements
                        and pin_positions is not None
                        and connections_by_id is not None
                        and not _wire_is_safe_for_context(
                            shifted,
                            placements=placements,
                            pin_positions=pin_positions,
                            connections_by_id=connections_by_id,
                            junction_nodes=junction_nodes,
                        )
                    ):
                        continue
                    updated[connection_id] = shifted
                    shifted_count += 1

    spaced = tuple(updated.get(wire.connection_id, wire) for wire in wires)
    return spaced, shifted_count


def _offset_single_segment_wire(
    wire: WirePath,
    segment: Segment,
    *,
    offset: float,
) -> WirePath:
    if abs(offset) <= _COORD_EPS:
        return wire

    if _segment_axis(segment) == "horizontal":
        shifted_y = segment.start.y + offset
        points = (
            segment.start,
            Point2D(segment.start.x, shifted_y),
            Point2D(segment.end.x, shifted_y),
            segment.end,
        )
    else:
        shifted_x = segment.start.x + offset
        points = (
            segment.start,
            Point2D(shifted_x, segment.start.y),
            Point2D(shifted_x, segment.end.y),
            segment.end,
        )
    deduped = _dedupe_points(list(points))
    return WirePath(
        connection_id=wire.connection_id,
        points=deduped,
        segments=points_to_segments(deduped),
    )


def _offset_segment_in_wire(
    wire: WirePath,
    *,
    segment_index: int,
    offset: float,
) -> WirePath:
    if abs(offset) <= _COORD_EPS:
        return wire
    if segment_index < 0 or segment_index >= len(wire.segments):
        return wire

    segment = wire.segments[segment_index]
    if len(wire.segments) == 1:
        return _offset_single_segment_wire(wire, segment, offset=offset)
    if len(wire.segments) > 2 and (
        segment_index == 0 or segment_index == len(wire.segments) - 1
    ):
        return wire

    points = list(wire.points)
    start = points[segment_index]
    end = points[segment_index + 1]
    rebuilt = points[:segment_index]

    if _segment_axis(segment) == "horizontal":
        shifted_y = segment.start.y + offset
        shifted_start = Point2D(start.x, shifted_y)
        shifted_end = Point2D(end.x, shifted_y)
    else:
        shifted_x = segment.start.x + offset
        shifted_start = Point2D(shifted_x, start.y)
        shifted_end = Point2D(shifted_x, end.y)

    rebuilt.extend((start, shifted_start, shifted_end, end))
    rebuilt.extend(points[segment_index + 2 :])

    deduped = _dedupe_points(rebuilt)
    return WirePath(
        connection_id=wire.connection_id,
        points=deduped,
        segments=points_to_segments(deduped),
    )


def _find_segment_index(wire: WirePath, target: Segment) -> int | None:
    target_key = _segment_key(target)
    for index, segment in enumerate(wire.segments):
        if _segment_key(segment) == target_key:
            return index
    return None


def _apply_track_spacing_pass(
    wires: Sequence[WirePath],
    *,
    placements: Sequence[ComponentPlacement] = (),
    pin_positions: Mapping[str, Point2D] | None = None,
    connections_by_id: Mapping[str, Connection] | None = None,
    junction_nodes: frozenset[Point2D] = frozenset(),
) -> tuple[tuple[WirePath, ...], int]:
    """Apply one deterministic spacing pass across currently overlapping tracks."""

    wire_by_id = {wire.connection_id: wire for wire in wires}
    updated: dict[str, WirePath] = {}
    shifted_count = 0

    horizontal_groups: dict[float, list[tuple[str, int, Segment]]] = {}
    vertical_groups: dict[float, list[tuple[str, int, Segment]]] = {}
    for wire in wires:
        for segment_index, segment in enumerate(wire.segments):
            if _segment_axis(segment) == "horizontal":
                horizontal_groups.setdefault(round(segment.start.y, 6), []).append(
                    (wire.connection_id, segment_index, segment)
                )
            else:
                vertical_groups.setdefault(round(segment.start.x, 6), []).append(
                    (wire.connection_id, segment_index, segment)
                )

    for groups in (horizontal_groups, vertical_groups):
        for wire_segments in groups.values():
            components = _overlap_components(
                tuple((connection_id, segment) for connection_id, _index, segment in wire_segments)
            )
            for component in components:
                ordered = sorted(
                    (
                        (
                            connection_id,
                            segment,
                        )
                        for connection_id, segment in component
                    ),
                    key=lambda item: item[0],
                )
                for offset_index, (connection_id, original_segment) in zip(
                    _track_offsets(len(ordered)),
                    ordered,
                ):
                    if offset_index == 0:
                        continue
                    current_wire = updated.get(connection_id, wire_by_id[connection_id])
                    segment_index = _find_segment_index(current_wire, original_segment)
                    if segment_index is None:
                        continue
                    shifted = _offset_segment_in_wire(
                        current_wire,
                        segment_index=segment_index,
                        offset=offset_index * WIRE_TRACK_SPACING,
                    )
                    if shifted == current_wire:
                        continue
                    if (
                        placements
                        and pin_positions is not None
                        and connections_by_id is not None
                        and not _wire_is_safe_for_context(
                            shifted,
                            placements=placements,
                            pin_positions=pin_positions,
                            connections_by_id=connections_by_id,
                            junction_nodes=junction_nodes,
                        )
                    ):
                        continue
                    updated[connection_id] = shifted
                    shifted_count += 1

    spaced = tuple(updated.get(wire.connection_id, wire) for wire in wires)
    return spaced, shifted_count


def apply_track_spacing(
    wires: Sequence[WirePath],
    *,
    placements: Sequence[ComponentPlacement] = (),
    pin_positions: Mapping[str, Point2D] | None = None,
    connections_by_id: Mapping[str, Connection] | None = None,
    junction_nodes: frozenset[Point2D] = frozenset(),
) -> tuple[tuple[WirePath, ...], int]:
    """Deterministically offset overlapping wire trunks onto nearby tracks."""

    current = tuple(wires)
    total_shifted = 0
    current, shifted_count = _apply_shared_segment_split_pass(
        current,
        placements=placements,
        pin_positions=pin_positions,
        connections_by_id=connections_by_id,
        junction_nodes=junction_nodes,
    )
    total_shifted += shifted_count
    for _pass in range(_MAX_TRACK_SPACING_PASSES):
        current, shifted_count = _apply_track_spacing_pass(
            current,
            placements=placements,
            pin_positions=pin_positions,
            connections_by_id=connections_by_id,
            junction_nodes=junction_nodes,
        )
        total_shifted += shifted_count
        if shifted_count == 0:
            break
    return current, total_shifted


def build_routing_report(
    wires: Sequence[WirePath],
    *,
    junction_nodes: frozenset[Point2D],
    placements: Sequence[ComponentPlacement] = (),
    pin_positions: Mapping[str, Point2D] | None = None,
    connections_by_id: Mapping[str, Connection] | None = None,
    detoured_path_count: int = 0,
    spaced_track_count: int = 0,
) -> RoutingReport:
    """Build machine-readable diagnostics for an already-routed wire set."""

    issues: list[RoutingIssue] = []
    junction_keys = {(round(node.x, 6), round(node.y, 6)) for node in junction_nodes}

    for left_index, left_wire in enumerate(wires):
        for right_wire in wires[left_index + 1 :]:
            same_net_branch = _same_net_branch_family(left_wire, right_wire)
            for left_segment in left_wire.segments:
                for right_segment in right_wire.segments:
                    if _segment_key(left_segment) == _segment_key(right_segment):
                        if same_net_branch:
                            continue
                        issues.append(
                            RoutingIssue(
                                kind="shared_segment",
                                severity=_routing_issue_severity("shared_segment"),
                                connection_ids=tuple(
                                    sorted((left_wire.connection_id, right_wire.connection_id))
                                ),
                                segment_axis=_segment_axis(left_segment),
                                location=None,
                                detail="two wire paths share the same routed segment",
                            )
                        )
                        continue

                    overlap = _overlap_length(left_segment, right_segment)
                    if overlap > _COORD_EPS:
                        if same_net_branch:
                            continue
                        issues.append(
                            RoutingIssue(
                                kind="parallel_overlap",
                                severity=_routing_issue_severity("parallel_overlap"),
                                connection_ids=tuple(
                                    sorted((left_wire.connection_id, right_wire.connection_id))
                                ),
                                segment_axis=_segment_axis(left_segment),
                                location=None,
                                detail="two wire paths overlap on the same routing track",
                            )
                        )
                        continue

                    if segments_intersect(left_segment, right_segment):
                        if same_net_branch:
                            continue
                        point = _crossing_point(left_segment, right_segment)
                        if point is None:
                            continue
                        key = (round(point.x, 6), round(point.y, 6))
                        if key in junction_keys:
                            continue
                        issues.append(
                            RoutingIssue(
                                kind="crossing_without_junction",
                                severity=_routing_issue_severity("crossing_without_junction"),
                                connection_ids=tuple(
                                    sorted((left_wire.connection_id, right_wire.connection_id))
                                ),
                                segment_axis="crossing",
                                location=point,
                                detail="wire crossing is not declared as an electrical junction",
                            )
                        )

    issue_list = list(dict.fromkeys(issues))
    if placements and connections_by_id:
        for wire in wires:
            try:
                connection = connection_for_wire(wire, connections_by_id)
            except KeyError:
                continue
            owner_ids = {connection.port_a.owner_id, connection.port_b.owner_id}
            for placement in placements:
                if placement.element_id in owner_ids:
                    continue
                bbox = _placement_bbox(placement)
                hit_segment = next(
                    (
                        segment
                        for segment in wire.segments
                        if _segment_passes_through_bbox(segment, bbox)
                    ),
                    None,
                )
                if hit_segment is None:
                    continue
                issue_list.append(
                    RoutingIssue(
                        kind="wire_through_component",
                        severity=_routing_issue_severity("wire_through_component"),
                        connection_ids=(wire.connection_id,),
                        segment_axis=_segment_axis(hit_segment),
                        location=None,
                        detail=f"wire path passes through component {placement.element_id}",
                    )
                )
    if pin_positions and connections_by_id:
        junction_keys = {(round(node.x, 6), round(node.y, 6)) for node in junction_nodes}
        pin_name_by_id = {
            connection.port_a.id: f"{connection.port_a.owner_id}.{connection.port_a.name}"
            for connection in connections_by_id.values()
        } | {
            connection.port_b.id: f"{connection.port_b.owner_id}.{connection.port_b.name}"
            for connection in connections_by_id.values()
        }
        for wire in wires:
            try:
                connection = connection_for_wire(wire, connections_by_id)
            except KeyError:
                continue
            connected_pin_ids = {connection.port_a.id, connection.port_b.id}
            connected_pin_ids |= _wire_net_branch_pin_ids(wire)
            branch_owner_ids = _wire_net_branch_owner_ids(wire)
            for pin_id, pin_point in pin_positions.items():
                if pin_id in connected_pin_ids:
                    continue
                if branch_owner_ids and _pin_owner_id(pin_id) in branch_owner_ids:
                    continue
                if (round(pin_point.x, 6), round(pin_point.y, 6)) in junction_keys:
                    continue
                hit_segment = next(
                    (segment for segment in wire.segments if _segment_near_pin(segment, pin_point)),
                    None,
                )
                if hit_segment is None:
                    continue
                issue_list.append(
                    RoutingIssue(
                        kind="wire_near_unconnected_pin",
                        severity=_routing_issue_severity("wire_near_unconnected_pin"),
                        connection_ids=(wire.connection_id,),
                        segment_axis=_segment_axis(hit_segment),
                        location=pin_point,
                        detail=(
                            "wire path passes near unconnected pin "
                            f"{pin_name_by_id.get(pin_id, pin_id)}"
                        ),
                    )
                )
    unique_issues = tuple(dict.fromkeys(issue_list))
    highest_severity = None
    if unique_issues:
        highest_severity = max(
            (issue.severity for issue in unique_issues),
            key=lambda severity: _SEVERITY_RANK[severity],
        )
    return RoutingReport(
        issues=unique_issues,
        highest_severity=highest_severity,
        detoured_path_count=detoured_path_count,
        spaced_track_count=spaced_track_count,
        has_attention_items=bool(unique_issues),
    )


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
