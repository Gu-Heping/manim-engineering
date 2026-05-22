"""
Build two resistors and connect them in a semantic graph — no render.

Phase 2 exit example: component pins attach to CircuitGraph topology.
"""

from manim_engineering.components import Resistor
from manim_engineering.semantic import CircuitGraph


def main() -> None:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)

    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    print(f"nodes: {[n.id for n in graph.nodes]}")
    print(f"connected: {graph.are_connected(r1.get_pin('b'), r2.get_pin('a'))}")


if __name__ == "__main__":
    main()
