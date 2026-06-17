"""MinimalRenderer digital gate symbol coverage."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Dot

from manim_engineering.components import ANDGate, NOTGate, ORGate
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer


def test_binary_gate_symbols_are_distinct_and_deterministic() -> None:
    renderer = MinimalRenderer()
    and_first = renderer.render(ANDGate("and1"))
    and_second = renderer.render(ANDGate("and1"))
    or_gate = renderer.render(ORGate("or1"))

    assert len(and_first.submobjects) == 2  # body + pin dots
    assert len(or_gate.submobjects) == 2
    assert np.allclose(and_first.get_all_points(), and_second.get_all_points())
    and_points = and_first.submobjects[0].get_all_points()
    or_points = or_gate.submobjects[0].get_all_points()
    assert and_points.shape != or_points.shape or not np.allclose(and_points, or_points)


def test_not_gate_symbol_has_inversion_bubble() -> None:
    mob = MinimalRenderer().render(NOTGate("inv1", label="INV"))
    body = mob.submobjects[0]

    assert len(mob.submobjects) == 3  # body + pin dots + label
    assert any(isinstance(child, Dot) for child in body.submobjects)


def test_gate_layout_preserves_renderer_metadata() -> None:
    graph = CircuitGraph()
    and_gate = ANDGate("and1")
    inv = NOTGate("inv1")
    graph.add(and_gate)
    graph.add(inv)
    graph.connect(and_gate.port_out, inv.port_in)
    elements = {"and1": and_gate, "inv1": inv}
    layout = LayoutEngine().layout(graph, elements)

    scene = MinimalRenderer().render_layout(layout, graph, elements)

    rendered_components = scene.submobjects[: len(layout.placements)]
    assert [mob.element_id for mob in rendered_components] == [
        placement.element_id for placement in layout.placements
    ]
    assert all(
        getattr(child, "element_id", None) == mob.element_id
        for mob in rendered_components
        for child in mob.get_family()
    )
