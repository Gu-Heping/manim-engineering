"""LayoutEngine.solve is an alias for layout."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine


def test_layout_engine_solve_matches_layout() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    circuit.add(r1)
    circuit.add(r2)
    circuit.connect(r1.get_port("b"), r2.get_port("a"))

    engine = LayoutEngine()
    elements = {"r1": r1, "r2": r2}
    assert engine.solve(circuit, elements) == engine.layout(circuit, elements)
