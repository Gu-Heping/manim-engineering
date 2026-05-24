"""Port.id stability contract — documents live-ID semantics for connections."""

from __future__ import annotations

from manim_engineering.core import (
    CircuitGraph,
    Node,
    PinDirection,
    SignalType,
)


def _wired_pair() -> tuple[Node, Node, CircuitGraph]:
    src = Node(id="src")
    src.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)
    dst = Node(id="dst")
    dst.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    graph = CircuitGraph()
    graph.add_node(src)
    graph.add_node(dst)
    graph.connect(src.get_pin("out"), dst.get_pin("in"))
    return src, dst, graph


def test_port_id_stable_after_connect() -> None:
    src, dst, graph = _wired_pair()
    out_pin = src.get_pin("out")
    in_pin = dst.get_pin("in")
    assert out_pin.id == "src.out"
    assert in_pin.id == "dst.in"
    conns = graph.get_connections(out_pin)
    assert len(conns) == 1
    assert conns[0].involves(out_pin)
    assert conns[0].other_port(out_pin) is in_pin


def test_connection_involves_matches_other_port_live_id() -> None:
    src, dst, graph = _wired_pair()
    out_pin = src.get_pin("out")
    conn = graph.get_connections(out_pin)[0]
    assert conn.involves(out_pin)
    assert conn.other_port(out_pin) is dst.get_pin("in")


def test_mutating_port_name_desynchronizes_graph_pair_index() -> None:
    """Renaming after connect is unsupported — pair index and connection id go stale."""
    src, dst, graph = _wired_pair()
    out_pin = src.get_pin("out")
    in_pin = dst.get_pin("in")
    conn = graph.get_connections(out_pin)[0]
    assert conn.id == "conn-dst.in--src.out"

    out_pin.name = "renamed"
    assert out_pin.id == "src.renamed"
    # Connection still references the same Port object; live id comparison still matches.
    assert conn.involves(out_pin)
    assert conn.other_port(out_pin) is in_pin
    # Graph pair index was keyed at connect time with old ids — queries break.
    assert not graph.are_connected(out_pin, in_pin)
