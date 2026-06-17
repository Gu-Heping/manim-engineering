"""IEC renderer variant smoke and determinism tests."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Rectangle

from manim_engineering.components import NMOS, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.iec import IECManimRenderer, IECRenderer
from manim_engineering.renderers.iec import theme as iec_theme
from manim_engineering.renderers.minimal import MinimalRenderer
from manim_engineering.renderers.minimal import theme as minimal_theme


def _two_resistor_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    graph.add(r1)
    graph.add(r2)
    graph.connect(r1.port_b, r2.port_a)
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().solve(graph, elements)
    return graph, elements, layout


def test_iec_renderer_render_layout_is_deterministic() -> None:
    graph, elements, layout = _two_resistor_fixture()
    renderer = IECRenderer()

    first = renderer.render_layout(layout, graph, elements)
    second = renderer.render_layout(layout, graph, elements)

    assert np.allclose(first.get_all_points(), second.get_all_points())


def test_iec_resistor_uses_rectangular_body_without_component_state() -> None:
    resistor = Resistor("r1", label="R1")
    before = (resistor.semantic_type, tuple(sorted(resistor.pins)))
    minimal = MinimalRenderer().render(resistor)
    iec = IECRenderer().render(resistor)

    assert (resistor.semantic_type, tuple(sorted(resistor.pins))) == before
    assert any(isinstance(child, Rectangle) for child in iec.submobjects[0].submobjects)
    assert not any(isinstance(child, Rectangle) for child in minimal.submobjects[0].submobjects)
    assert (
        iec.get_all_points().shape != minimal.get_all_points().shape
        or not np.allclose(iec.get_all_points(), minimal.get_all_points())
    )


def test_iec_theme_exports_renderer_owned_surface() -> None:
    assert "POWER_COLOR" in iec_theme.__all__
    assert "color_for_signal_type" in iec_theme.__all__
    assert iec_theme.POWER_COLOR == minimal_theme.POWER_COLOR
    assert iec_theme.color_for_signal_type is minimal_theme.color_for_signal_type
    assert iec_theme.component_stroke_width() == minimal_theme.component_stroke_width()


def test_iec_manim_renderer_preserves_topology_metadata() -> None:
    graph, elements, layout = _two_resistor_fixture()
    topology = IECManimRenderer().render_topology(graph, layout, elements)

    assert [mob.element_id for mob in topology.components.submobjects] == [
        placement.element_id for placement in layout.placements
    ]
    assert {
        getattr(line, "connection_id")
        for line in topology.wire_lines()
        if hasattr(line, "connection_id")
    } == {wire.connection_id for wire in layout.wires}


def test_iec_renderer_uses_distinct_mosfet_convention_without_component_state() -> None:
    nmos = NMOS("m1", label="M1")
    before = (nmos.semantic_type, tuple(sorted(nmos.pins)))
    minimal = MinimalRenderer().render(nmos)
    iec = IECRenderer().render(nmos)

    assert (nmos.semantic_type, tuple(sorted(nmos.pins))) == before
    assert len(iec.submobjects) == len(minimal.submobjects)
    iec_points = iec.get_all_points()
    minimal_points = minimal.get_all_points()
    assert (
        iec_points.shape != minimal_points.shape
        or not np.allclose(iec_points, minimal_points)
    )
