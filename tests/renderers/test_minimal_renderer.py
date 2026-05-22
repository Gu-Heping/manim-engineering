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
    assert len(mob.submobjects) == 3  # body, pin dots, label


def test_render_layout_includes_components_and_wires() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    scene = MinimalRenderer().render_layout(layout, graph, elements)

    # Two resistor groups (body+label each) + wire segments
    assert len(scene.submobjects) >= 3


def test_render_layout_separates_placed_components() -> None:
    from manim_engineering.components import Capacitor

    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    graph.add(r1)
    graph.add(c1)
    graph.connect(r1.port_b, c1.port_a)

    elements = {"r1": r1, "c1": c1}
    layout = LayoutEngine().solve(graph, elements)
    scene = MinimalRenderer().render_layout(layout, graph, elements)

    by_id = {p.element_id: scene.submobjects[i] for i, p in enumerate(layout.placements)}
    c1_x = by_id["c1"].get_all_points()[:, 0]
    r1_x = by_id["r1"].get_all_points()[:, 0]
    assert float(r1_x.max()) < float(c1_x.min()) - 0.1


def test_render_layout_deterministic_points() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    renderer = MinimalRenderer()
    first = renderer.render_layout(layout, graph, elements)
    second = renderer.render_layout(layout, graph, elements)
    assert np.allclose(first.get_all_points(), second.get_all_points())
