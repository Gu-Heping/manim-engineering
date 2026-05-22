"""MinimalRenderer structure and determinism tests."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer
from manim_engineering.semantic import CircuitGraph


def _two_resistor_graph() -> tuple[CircuitGraph, Resistor, Resistor]:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    return graph, r1, r2


def test_minimal_renderer_module_importable() -> None:
    assert MinimalRenderer is not None


def test_render_resistor_deterministic_structure() -> None:
    renderer = MinimalRenderer()
    r1 = Resistor("r1", label="R1")
    first = renderer.render(r1)
    second = renderer.render(r1)

    assert len(first.submobjects) == len(second.submobjects)
    assert np.allclose(first.get_all_points(), second.get_all_points())


def test_render_resistor_has_body_and_label() -> None:
    mob = MinimalRenderer().render(Resistor("r1", label="R1"))
    assert len(mob.submobjects) == 2


def test_render_layout_includes_components_and_wires() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    scene = MinimalRenderer().render_layout(layout, graph, elements)

    # Two resistor groups (body+label each) + wire segments
    assert len(scene.submobjects) >= 3


def test_render_layout_deterministic_points() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    renderer = MinimalRenderer()
    first = renderer.render_layout(layout, graph, elements)
    second = renderer.render_layout(layout, graph, elements)
    assert np.allclose(first.get_all_points(), second.get_all_points())
