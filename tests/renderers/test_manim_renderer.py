"""ManimRenderer adapter delegates to MinimalRenderer."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer, MinimalRenderer


def test_manim_renderer_matches_minimal_render_circuit() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)
    circuit.connect(r1.port_b, r2.port_a)

    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(circuit, elements)

    minimal = MinimalRenderer().render_circuit(circuit, layout, elements)
    manim = ManimRenderer().render(circuit, layout, elements)
    assert np.allclose(minimal.get_all_points(), manim.get_all_points())


def test_manim_renderer_render_topology_splits_immutable_groups() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    circuit.add(r1)
    circuit.add(r2)
    circuit.connect(r1.port_b, r2.port_a)
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(circuit, elements)

    topology = ManimRenderer().render_topology(circuit, layout, elements)
    assert len(topology.components.submobjects) == 2
    assert len(topology.wires.submobjects) >= 1
    assert topology.n_components == 2
    assert len(topology.circuit_group.submobjects) == 2
