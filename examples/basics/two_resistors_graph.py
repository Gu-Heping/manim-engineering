"""
Build two resistors and connect them in a semantic graph — no render.

Phase 2 exit example: component ports attach to CircuitGraph topology.
"""

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph


def main() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)

    circuit.connect(r1.get_port("b"), r2.get_port("a"))

    print(f"nodes: {[n.id for n in circuit.nodes]}")
    print(f"connected: {circuit.are_connected(r1.get_port('b'), r2.get_port('a'))}")


if __name__ == "__main__":
    main()
