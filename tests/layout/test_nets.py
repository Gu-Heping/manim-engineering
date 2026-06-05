"""Electrical net grouping and star routing tests."""

from __future__ import annotations

from manim_engineering.components import Ground, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import (
    MIN_VISIBLE_STUB,
    LayoutEngine,
    apply_track_spacing,
    build_routing_report,
    group_connections_into_nets,
    net_id_for_pins,
)
from manim_engineering.layout.align import origin_for_pin_at
from manim_engineering.layout.nets import (
    WIRE_TRACK_SPACING,
    apply_wire_detours,
    connection_for_wire,
)
from manim_engineering.layout.types import ComponentPlacement, Point2D, Segment, WirePath


def _three_pin_net_graph():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r3 = Resistor("r3", label="R3")
    for element in (r1, r2, r3):
        element.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    graph.connect(r2.get_pin("a"), r3.get_pin("a"))
    return graph, {"r1": r1, "r2": r2, "r3": r3}


def test_group_connections_into_nets_merges_shared_pins() -> None:
    graph, _elements = _three_pin_net_graph()
    nets = group_connections_into_nets(graph.connections)
    assert len(nets) == 1
    assert nets[0].pin_ids == frozenset({"r1.b", "r2.a", "r3.a"})
    assert nets[0].net_id == net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))


def test_star_routing_uses_single_vertical_trunk() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    layout = LayoutEngine().layout(
        graph,
        elements,
        net_waypoints={net_id: hub},
    )
    vertical_at_hub = [
        wire
        for wire in layout.wires
        if any(
            seg.start.x == seg.end.x == hub.x and seg.start.y != seg.end.y
            for seg in wire.segments
        )
    ]
    assert vertical_at_hub


def test_star_net_hub_coincident_pin_gets_visible_stub() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    r2 = elements["r2"]
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides={r2.element_id: origin_for_pin_at(r2, "a", hub)},
        net_waypoints={net_id: hub},
    )
    hub_branch = next(
        wire for wire in layout.wires if wire.connection_id == f"{net_id}/r2.a"
    )
    assert len(hub_branch.segments) == 1
    seg = hub_branch.segments[0]
    length = abs(seg.end.x - seg.start.x) + abs(seg.end.y - seg.start.y)
    assert length >= MIN_VISIBLE_STUB - 1e-6


def test_connection_for_wire_resolves_net_branch_ids() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    layout = LayoutEngine().layout(
        graph,
        elements,
        net_waypoints={net_id: hub},
    )
    connections = {connection.id: connection for connection in graph.connections}
    net_wires = [wire for wire in layout.wires if wire.connection_id.startswith("net-")]
    assert net_wires
    for wire in net_wires:
        connection = connection_for_wire(wire, connections)
        assert connection.id in connections


def test_build_routing_report_ignores_benign_same_net_branch_overlap_and_pin_proximity() -> None:
    graph, elements = _three_pin_net_graph()
    hub = Point2D(0.0, 0.0)
    net_id = net_id_for_pins(frozenset({"r1.b", "r2.a", "r3.a"}))
    layout = LayoutEngine().layout(
        graph,
        elements,
        net_waypoints={net_id: hub},
    )

    issue_kinds = {issue.kind for issue in layout.routing_report.issues}
    assert "shared_segment" not in issue_kinds
    assert "parallel_overlap" not in issue_kinds
    assert "wire_near_unconnected_pin" not in issue_kinds


def test_build_routing_report_detects_shared_segment_and_parallel_overlap() -> None:
    shared_a = WirePath(
        connection_id="c1",
        points=(Point2D(0.0, 0.0), Point2D(1.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(1.0, 0.0)),),
    )
    shared_b = WirePath(
        connection_id="c2",
        points=(Point2D(0.0, 0.0), Point2D(1.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(1.0, 0.0)),),
    )
    overlap_b = WirePath(
        connection_id="c3",
        points=(Point2D(0.5, 0.0), Point2D(1.5, 0.0)),
        segments=(Segment(Point2D(0.5, 0.0), Point2D(1.5, 0.0)),),
    )

    report = build_routing_report((shared_a, shared_b, overlap_b), junction_nodes=frozenset())

    kinds = {issue.kind for issue in report.issues}
    assert "shared_segment" in kinds
    assert "parallel_overlap" in kinds
    assert {issue.severity for issue in report.issues} == {"cosmetic"}
    assert report.highest_severity == "cosmetic"
    assert report.has_attention_items is True


def test_build_routing_report_ignores_declared_junction_crossing() -> None:
    left = WirePath(
        connection_id="left",
        points=(Point2D(-1.0, 0.0), Point2D(1.0, 0.0)),
        segments=(Segment(Point2D(-1.0, 0.0), Point2D(1.0, 0.0)),),
    )
    right = WirePath(
        connection_id="right",
        points=(Point2D(0.0, -1.0), Point2D(0.0, 1.0)),
        segments=(Segment(Point2D(0.0, -1.0), Point2D(0.0, 1.0)),),
    )

    clean = build_routing_report((left, right), junction_nodes=frozenset({Point2D(0.0, 0.0)}))
    warned = build_routing_report((left, right), junction_nodes=frozenset())

    assert clean.issues == ()
    assert any(issue.kind == "crossing_without_junction" for issue in warned.issues)


def test_build_routing_report_detects_wire_near_unconnected_pin() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    gnd = Ground("gnd", label="GND")
    for element in (r1, r2, gnd):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),),
    )
    report = build_routing_report(
        (wire,),
        junction_nodes=frozenset(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.0, 0.0),
            gnd.get_pin("gnd").id: Point2D(1.0, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
    )

    hits = [issue for issue in report.issues if issue.kind == "wire_near_unconnected_pin"]
    assert hits
    assert hits[0].severity == "ambiguous"
    assert hits[0].location == Point2D(1.0, 0.02)
    assert "gnd.gnd" in hits[0].detail


def test_apply_wire_detours_reroutes_away_from_unconnected_pin() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    gnd = Ground("gnd", label="GND")
    for element in (r1, r2, gnd):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),),
    )

    detoured, count = apply_wire_detours(
        (wire,),
        placements=(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.0, 0.0),
            gnd.get_pin("gnd").id: Point2D(1.0, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    assert detoured[0].points[0] == wire.points[0]
    assert detoured[0].points[-1] == wire.points[-1]
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.0, 0.0),
            gnd.get_pin("gnd").id: Point2D(1.0, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_near_unconnected_pin" for issue in report.issues)


def test_apply_wire_detours_reroutes_through_component_body() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r3 = Resistor("r3", label="R3")
    for element in (r1, r2, r3):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r3.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),),
    )

    placements = (
        ComponentPlacement(
            element_id="r2",
            origin=Point2D(0.8, -0.1),
            bounds=r2.get_bounds(),
        ),
    )
    detoured, count = apply_wire_detours(
        (wire,),
        placements=placements,
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r3.get_pin("a").id: Point2D(2.0, 0.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    assert detoured[0].points[0] == wire.points[0]
    assert detoured[0].points[-1] == wire.points[-1]
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        placements=placements,
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r3.get_pin("a").id: Point2D(2.0, 0.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_through_component" for issue in report.issues)


def test_apply_wire_detours_reroutes_through_multiple_component_bodies() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r3 = Resistor("r3", label="R3")
    r4 = Resistor("r4", label="R4")
    for element in (r1, r2, r3, r4):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r4.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(3.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(3.0, 0.0)),),
    )

    placements = (
        ComponentPlacement(
            element_id="r2",
            origin=Point2D(0.8, -0.1),
            bounds=r2.get_bounds(),
        ),
        ComponentPlacement(
            element_id="r3",
            origin=Point2D(1.8, -0.1),
            bounds=r3.get_bounds(),
        ),
    )
    detoured, count = apply_wire_detours(
        (wire,),
        placements=placements,
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r4.get_pin("a").id: Point2D(3.0, 0.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        placements=placements,
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r4.get_pin("a").id: Point2D(3.0, 0.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_through_component" for issue in report.issues)


def test_apply_wire_detours_reroutes_away_from_multiple_unconnected_pins() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    g1 = Ground("g1", label="G1")
    g2 = Ground("g2", label="G2")
    for element in (r1, r2, g1, g2):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(2.5, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(2.5, 0.0)),),
    )

    detoured, count = apply_wire_detours(
        (wire,),
        placements=(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.5, 0.0),
            g1.get_pin("gnd").id: Point2D(0.9, 0.02),
            g2.get_pin("gnd").id: Point2D(1.8, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.5, 0.0),
            g1.get_pin("gnd").id: Point2D(0.9, 0.02),
            g2.get_pin("gnd").id: Point2D(1.8, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_near_unconnected_pin" for issue in report.issues)


def test_apply_wire_detours_can_flip_two_segment_l_path_when_both_legs_are_blocked() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    g1 = Ground("g1", label="G1")
    g2 = Ground("g2", label="G2")
    for element in (r1, r2, g1, g2):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(Point2D(0.0, 0.0), Point2D(2.0, 0.0), Point2D(2.0, 2.0)),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
            Segment(Point2D(2.0, 0.0), Point2D(2.0, 2.0)),
        ),
    )

    detoured, count = apply_wire_detours(
        (wire,),
        placements=(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.0, 2.0),
            g1.get_pin("gnd").id: Point2D(1.0, 0.02),
            g2.get_pin("gnd").id: Point2D(1.98, 1.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    assert detoured[0].points == (
        Point2D(0.0, 0.0),
        Point2D(0.0, 2.0),
        Point2D(2.0, 2.0),
    )
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(2.0, 2.0),
            g1.get_pin("gnd").id: Point2D(1.0, 0.02),
            g2.get_pin("gnd").id: Point2D(1.98, 1.0),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_near_unconnected_pin" for issue in report.issues)


def test_apply_wire_detours_can_flip_local_corner_in_longer_path() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    g1 = Ground("g1", label="G1")
    for element in (r1, r2, g1):
        element.attach_to(graph)
    connection = graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    wire = WirePath(
        connection_id=connection.id,
        points=(
            Point2D(0.0, 0.0),
            Point2D(2.0, 0.0),
            Point2D(2.0, 2.0),
            Point2D(4.0, 2.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
            Segment(Point2D(2.0, 0.0), Point2D(2.0, 2.0)),
            Segment(Point2D(2.0, 2.0), Point2D(4.0, 2.0)),
        ),
    )

    detoured, count = apply_wire_detours(
        (wire,),
        placements=(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(4.0, 2.0),
            g1.get_pin("gnd").id: Point2D(1.0, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        junction_nodes=frozenset(),
    )

    assert count == 1
    assert detoured[0].points == (
        Point2D(0.0, 0.0),
        Point2D(0.0, 2.0),
        Point2D(2.0, 2.0),
        Point2D(4.0, 2.0),
    )
    report = build_routing_report(
        detoured,
        junction_nodes=frozenset(),
        pin_positions={
            r1.get_pin("b").id: Point2D(0.0, 0.0),
            r2.get_pin("a").id: Point2D(4.0, 2.0),
            g1.get_pin("gnd").id: Point2D(1.0, 0.02),
        },
        connections_by_id={connection.id: connection for connection in graph.connections},
        detoured_path_count=count,
    )
    assert report.detoured_path_count == 1
    assert not any(issue.kind == "wire_near_unconnected_pin" for issue in report.issues)


def test_apply_track_spacing_offsets_overlapping_middle_trunks() -> None:
    left = WirePath(
        connection_id="left",
        points=(
            Point2D(0.0, 0.0),
            Point2D(0.0, 1.0),
            Point2D(3.0, 1.0),
            Point2D(3.0, 2.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(0.0, 1.0)),
            Segment(Point2D(0.0, 1.0), Point2D(3.0, 1.0)),
            Segment(Point2D(3.0, 1.0), Point2D(3.0, 2.0)),
        ),
    )
    right = WirePath(
        connection_id="right",
        points=(
            Point2D(0.5, 0.0),
            Point2D(0.5, 1.0),
            Point2D(2.5, 1.0),
            Point2D(2.5, 2.0),
        ),
        segments=(
            Segment(Point2D(0.5, 0.0), Point2D(0.5, 1.0)),
            Segment(Point2D(0.5, 1.0), Point2D(2.5, 1.0)),
            Segment(Point2D(2.5, 1.0), Point2D(2.5, 2.0)),
        ),
    )

    spaced, shifted = apply_track_spacing((left, right))

    assert shifted == 1
    assert spaced[0].points[0] == left.points[0]
    assert spaced[0].points[-1] == left.points[-1]
    assert spaced[1].points[0] == right.points[0]
    assert spaced[1].points[-1] == right.points[-1]
    assert any(len(wire.points) > 4 for wire in spaced)

    report = build_routing_report(spaced, junction_nodes=frozenset())
    assert not any(issue.kind == "parallel_overlap" for issue in report.issues)


def test_apply_track_spacing_can_rewrite_multiple_trunks_on_one_wire() -> None:
    main = WirePath(
        connection_id="mid",
        points=(
            Point2D(0.0, 0.0),
            Point2D(0.0, 1.0),
            Point2D(2.0, 1.0),
            Point2D(2.0, 3.0),
            Point2D(4.0, 3.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(0.0, 1.0)),
            Segment(Point2D(0.0, 1.0), Point2D(2.0, 1.0)),
            Segment(Point2D(2.0, 1.0), Point2D(2.0, 3.0)),
            Segment(Point2D(2.0, 3.0), Point2D(4.0, 3.0)),
        ),
    )
    horizontal = WirePath(
        connection_id="a_h",
        points=(
            Point2D(0.5, 0.0),
            Point2D(0.5, 1.0),
            Point2D(1.5, 1.0),
            Point2D(1.5, 2.0),
        ),
        segments=(
            Segment(Point2D(0.5, 0.0), Point2D(0.5, 1.0)),
            Segment(Point2D(0.5, 1.0), Point2D(1.5, 1.0)),
            Segment(Point2D(1.5, 1.0), Point2D(1.5, 2.0)),
        ),
    )
    vertical = WirePath(
        connection_id="a_v",
        points=(
            Point2D(1.0, 2.0),
            Point2D(2.0, 2.0),
            Point2D(2.0, 4.0),
        ),
        segments=(
            Segment(Point2D(1.0, 2.0), Point2D(2.0, 2.0)),
            Segment(Point2D(2.0, 2.0), Point2D(2.0, 4.0)),
        ),
    )

    spaced, shifted = apply_track_spacing((main, horizontal, vertical))

    assert shifted >= 2
    shifted_main = next(wire for wire in spaced if wire.connection_id == "mid")
    assert shifted_main.points[0] == main.points[0]
    assert shifted_main.points[-1] == main.points[-1]
    assert len(shifted_main.points) > len(main.points)

    report = build_routing_report(spaced, junction_nodes=frozenset())
    assert not any(issue.kind == "parallel_overlap" for issue in report.issues)


def test_apply_track_spacing_runs_multiple_passes_until_stable() -> None:
    base = WirePath(
        connection_id="a",
        points=(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
        segments=(Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),),
    )
    overlap = WirePath(
        connection_id="b",
        points=(Point2D(0.5, 0.0), Point2D(2.5, 0.0)),
        segments=(Segment(Point2D(0.5, 0.0), Point2D(2.5, 0.0)),),
    )
    nearby_track = WirePath(
        connection_id="c",
        points=(Point2D(0.5, WIRE_TRACK_SPACING), Point2D(2.5, WIRE_TRACK_SPACING)),
        segments=(
            Segment(
                Point2D(0.5, WIRE_TRACK_SPACING),
                Point2D(2.5, WIRE_TRACK_SPACING),
            ),
        ),
    )

    spaced, shifted = apply_track_spacing((base, overlap, nearby_track))

    assert shifted >= 2
    report = build_routing_report(spaced, junction_nodes=frozenset())
    assert not any(issue.kind == "parallel_overlap" for issue in report.issues)


def test_apply_track_spacing_can_rewrite_first_segment_of_multi_segment_wire() -> None:
    left = WirePath(
        connection_id="left",
        points=(
            Point2D(0.0, 0.0),
            Point2D(2.0, 0.0),
            Point2D(2.0, 1.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
            Segment(Point2D(2.0, 0.0), Point2D(2.0, 1.0)),
        ),
    )
    right = WirePath(
        connection_id="right",
        points=(
            Point2D(0.5, 0.0),
            Point2D(2.5, 0.0),
            Point2D(2.5, 1.0),
        ),
        segments=(
            Segment(Point2D(0.5, 0.0), Point2D(2.5, 0.0)),
            Segment(Point2D(2.5, 0.0), Point2D(2.5, 1.0)),
        ),
    )

    spaced, shifted = apply_track_spacing((left, right))

    assert shifted >= 1
    assert spaced[0].points[0] == left.points[0]
    assert spaced[1].points[0] == right.points[0]
    assert any(
        len(wire.points) > len(original.points)
        for wire, original in zip(spaced, (left, right))
    )

    report = build_routing_report(spaced, junction_nodes=frozenset())
    assert not any(issue.kind == "parallel_overlap" for issue in report.issues)


def test_apply_track_spacing_splits_shared_first_segment_of_longer_paths() -> None:
    upper = WirePath(
        connection_id="upper",
        points=(
            Point2D(0.0, 0.0),
            Point2D(2.0, 0.0),
            Point2D(2.0, 1.0),
            Point2D(3.0, 1.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
            Segment(Point2D(2.0, 0.0), Point2D(2.0, 1.0)),
            Segment(Point2D(2.0, 1.0), Point2D(3.0, 1.0)),
        ),
    )
    lower = WirePath(
        connection_id="lower",
        points=(
            Point2D(0.0, 0.0),
            Point2D(2.0, 0.0),
            Point2D(2.0, -1.0),
            Point2D(3.0, -1.0),
        ),
        segments=(
            Segment(Point2D(0.0, 0.0), Point2D(2.0, 0.0)),
            Segment(Point2D(2.0, 0.0), Point2D(2.0, -1.0)),
            Segment(Point2D(2.0, -1.0), Point2D(3.0, -1.0)),
        ),
    )

    spaced, shifted = apply_track_spacing((upper, lower))

    assert shifted >= 1
    assert spaced[0].points[0] == upper.points[0]
    assert spaced[1].points[0] == lower.points[0]
    report = build_routing_report(spaced, junction_nodes=frozenset())
    assert not any(issue.kind == "shared_segment" for issue in report.issues)
