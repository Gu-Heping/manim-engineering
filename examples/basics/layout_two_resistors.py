"""
Place two resistors on a grid, route their connection — no render.

Phase 3 exit example: layout consumes component hints and graph topology.
"""

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine


def main() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)
    circuit.connect(r1.get_port("b"), r2.get_port("a"))

    result = LayoutEngine().solve(circuit, {"r1": r1, "r2": r2})

    for placement in result.placements:
        print(f"{placement.element_id}: origin=({placement.origin.x}, {placement.origin.y})")

    for pin_id, position in sorted(result.pin_positions.items()):
        print(f"pin {pin_id}: ({position.x}, {position.y})")

    for wire in result.wires:
        pts = " → ".join(f"({p.x},{p.y})" for p in wire.points)
        print(f"wire {wire.connection_id}: {pts}")

    print(f"occupancy: {result.occupancy_ratio:.1%} of nominal frame")


if __name__ == "__main__":
    main()
