"""
Build a semantic circuit graph only — no Manim render.

Phase 1 exit example: topology + propagation without geometry.
"""

from manim_engineering.core import CircuitGraph, Node, PinDirection, SignalType
from manim_engineering.semantic import Bus, LogicLevel, LogicState, Signal


def main() -> None:
    graph = CircuitGraph()

    driver = Node(id="driver", label="Driver")
    driver.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)

    gate = Node(id="gate", label="Gate")
    gate.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)
    gate.add_pin("out", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)

    led = Node(id="led", label="LED")
    led.add_pin("in", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)

    for node in (driver, gate, led):
        graph.add_node(node)

    graph.connect(driver.get_pin("out"), gate.get_pin("in"))
    graph.connect(gate.get_pin("out"), led.get_pin("in"))

    clk = Signal(
        name="clk",
        signal_type=SignalType.CLOCK,
        value=LogicState(level=LogicLevel.LOW),
    )
    record = clk.propagate(driver.get_pin("out"), gate.get_pin("in"), graph=graph)

    bus = Bus.from_signals(
        "status",
        (
            (
                Signal(
                    name="ok",
                    signal_type=SignalType.DATA,
                    value=LogicState(level=LogicLevel.LOW),
                ),
                gate.get_pin("out"),
            ),
        ),
    )
    bus.propagate_lane(0, gate.get_pin("out"), led.get_pin("in"), graph=graph)

    print(f"graph nodes: {[n.id for n in graph.nodes]}")
    print(f"connections: {len(graph.connections)}")
    print(f"propagation: {record.state_transition}")


if __name__ == "__main__":
    main()
