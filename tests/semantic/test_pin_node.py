"""Pin and Node construction tests."""

from __future__ import annotations

import pytest

from manim_engineering.semantic import (
    ConnectionState,
    InvalidPinError,
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
    with pytest.raises(InvalidPinError):
        node.add_pin("a", direction=PinDirection.OUT, signal_type=SignalType.SIGNAL)


def test_node_get_pin_unknown_raises() -> None:
    node = Node(id="n1")
    with pytest.raises(InvalidPinError):
        node.get_pin("missing")
