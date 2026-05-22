"""MinimalRenderer.render_circuit composes graph + layout."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer


def test_render_circuit_matches_render_layout() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)
    circuit.connect(r1.get_port("b"), r2.get_port("a"))

    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(circuit, elements)
    renderer = MinimalRenderer()

    via_circuit = renderer.render_circuit(circuit, layout, elements)
    via_layout = renderer.render_layout(layout, circuit, elements)
    assert np.allclose(via_circuit.get_all_points(), via_layout.get_all_points())
