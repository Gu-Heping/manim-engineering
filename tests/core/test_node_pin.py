"""Node and Port (a.k.a. Pin) construction tests.

Owned by ``tests/core/`` because every assertion in this file exercises
core types only (``Node``, ``Port``, ``PinDirection``, ``ConnectionState``,
``SignalType``, ``InvalidPortError``). Previously lived in
``tests/semantic/test_pin_node.py``; moved as part of the A+B+D follow-up
de-duplication (E-2). The ``Pin`` symbol remains a Port alias exposed by
``manim_engineering.core`` for backward compatibility.
"""

from __future__ import annotations

import pytest

from manim_engineering.core import (
    ConnectionState,
    InvalidPortError,
    Node,
    PinDirection,
    SignalType,
)


def test_pin_construction_and_routing_hints() -> None:
    node = Node(id="u1", label="Buffer")
    pin = node.add_pin(
        "out",
        direction=PinDirection.OUT,
        signal_type=SignalType.DIGITAL,
        routing_hints=("east", "grid_row_2"),
    )
    assert pin.id == "u1.out"
    assert pin.owner_id == "u1"
    assert pin.direction == PinDirection.OUT
    assert pin.connection_state == ConnectionState.DISCONNECTED
    assert pin.routing_hints == ("east", "grid_row_2")


def test_node_duplicate_pin_raises() -> None:
    node = Node(id="n1")
    node.add_pin("a", direction=PinDirection.IN, signal_type=SignalType.SIGNAL)
    with pytest.raises(InvalidPortError):
        node.add_pin("a", direction=PinDirection.OUT, signal_type=SignalType.SIGNAL)


def test_node_get_pin_unknown_raises() -> None:
    node = Node(id="n1")
    with pytest.raises(InvalidPortError):
        node.get_pin("missing")
