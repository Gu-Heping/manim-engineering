"""CircuitGraph topology tests — no geometry."""

from __future__ import annotations

import pytest

from manim_engineering.semantic import (
    CircuitGraph,
    ConnectionState,
    InvalidConnectionError,
    InvalidPinError,
    Node,
    PinDirection,
    SignalType,
)


def _buffer_and_load() -> tuple[Node, Node]:
    buf = Node(id="buf", label="Buffer")
    buf.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)
    load = Node(id="load", label="Load")
    load.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    return buf, load


def test_graph_connect_and_query() -> None:
    graph = CircuitGraph()
    buf, load = _buffer_and_load()
    graph.add_node(buf)
    graph.add_node(load)

    conn = graph.connect(buf.get_pin("out"), load.get_pin("in"))
    assert conn.involves(buf.get_pin("out"))
    assert graph.are_connected(buf.get_pin("out"), load.get_pin("in"))
    assert buf.get_pin("out").connection_state == ConnectionState.CONNECTED
    assert load.get_pin("in").connection_state == ConnectionState.CONNECTED

    conns = graph.get_connections(buf.get_pin("out"))
    assert len(conns) == 1
    assert graph.neighbors(buf.get_pin("out")) == (load.get_pin("in"),)


def test_graph_disconnect() -> None:
    graph = CircuitGraph()
    buf, load = _buffer_and_load()
    graph.add_node(buf)
    graph.add_node(load)
    conn = graph.connect(buf.get_pin("out"), load.get_pin("in"))
    graph.disconnect(conn)
    assert not graph.are_connected(buf.get_pin("out"), load.get_pin("in"))
    assert buf.get_pin("out").connection_state == ConnectionState.DISCONNECTED


def test_graph_connect_unregistered_pin_raises() -> None:
    graph = CircuitGraph()
    buf, _ = _buffer_and_load()
    orphan = Node(id="orphan")
    orphan.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.SIGNAL)
    with pytest.raises(InvalidPinError):
        graph.connect(buf.get_pin("out"), orphan.get_pin("in"))


def test_graph_incompatible_direction_raises() -> None:
    graph = CircuitGraph()
    a = Node(id="a")
    b = Node(id="b")
    a.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.SIGNAL)
    b.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.SIGNAL)
    graph.add_node(a)
    graph.add_node(b)
    with pytest.raises(InvalidConnectionError):
        graph.connect(a.get_pin("out"), b.get_pin("out"))
