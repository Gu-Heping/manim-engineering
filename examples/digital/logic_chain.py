"""
Digital driver → gate → load: semantic graph and one propagation step.

Phase 8 digital example — no Manim render. For full bus + clock semantics see
``examples/basics/graph_only.py``.
"""

from manim_engineering.semantic import (
    CircuitGraph,
    LogicLevel,
    LogicState,
    Node,
    PinDirection,
    Signal,
    SignalType,
)


def main() -> None:
    graph = CircuitGraph()

    driver = Node(id="driver", label="Driver")
    driver.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)

    gate = Node(id="gate", label="Gate")
    gate.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    gate.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)

    load = Node(id="load", label="Load")
    load.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)

    for node in (driver, gate, load):
        graph.add_node(node)

    graph.connect(driver.get_pin("out"), gate.get_pin("in"))
    graph.connect(gate.get_pin("out"), load.get_pin("in"))

    edge = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    record = edge.propagate(driver.get_pin("out"), gate.get_pin("in"), graph=graph)

    print(f"nodes: {[n.id for n in graph.nodes]}")
    print(f"connections: {len(graph.connections)}")
    print(f"propagation: {record.state_transition}")


if __name__ == "__main__":
    main()
