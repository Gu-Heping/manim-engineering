"""Bus grouped topology tests."""

from __future__ import annotations

import pytest

from manim_engineering.semantic import (
    Bus,
    CircuitGraph,
    LogicLevel,
    LogicState,
    Node,
    PinDirection,
    Signal,
    SignalType,
    TopologyError,
)


def test_bus_propagate_all_deterministic_order() -> None:
    graph = CircuitGraph()
    driver = Node(id="drv")
    receiver = Node(id="rcv")
    for bit in ("d0", "d1"):
        driver.add_pin(bit, direction=PinDirection.OUT, signal_type=SignalType.DATA)
        receiver.add_pin(bit, direction=PinDirection.IN, signal_type=SignalType.DATA)
    graph.add_node(driver)
    graph.add_node(receiver)
    for bit in ("d0", "d1"):
        graph.connect(driver.get_pin(bit), receiver.get_pin(bit))

    pairs = tuple(
        (
            Signal(name=bit, signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW)),
            driver.get_pin(bit),
        )
        for bit in ("d0", "d1")
    )
    bus = Bus.from_signals("data_bus", pairs)
    edges = tuple((driver.get_pin(bit), receiver.get_pin(bit)) for bit in ("d0", "d1"))
    records = bus.propagate_all(edges, graph=graph)
    assert len(records) == 2
    assert records[0].to_pin_id == "rcv.d0"
    assert records[1].to_pin_id == "rcv.d1"


def test_bus_mismatched_lane_count_raises() -> None:
    node = Node(id="n")
    pin = node.add_pin("p", direction=PinDirection.OUT, signal_type=SignalType.DATA)
    bus = Bus.from_signals(
        "lane",
        ((Signal(name="s", signal_type=SignalType.DATA), pin),),
    )
    with pytest.raises(TopologyError):
        bus.propagate_all(())
