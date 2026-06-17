"""MinimalRenderer measurement probe symbol coverage."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim import Circle, Text

from manim_engineering.components import CurrentProbe, VoltageProbe
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer


def test_measurement_probe_symbols_are_distinct_and_deterministic() -> None:
    renderer = MinimalRenderer()
    voltage_first = renderer.render(VoltageProbe("vp1"))
    voltage_second = renderer.render(VoltageProbe("vp1"))
    current = renderer.render(CurrentProbe("ip1"))

    assert np.allclose(voltage_first.get_all_points(), voltage_second.get_all_points())
    voltage_body = voltage_first.submobjects[0]
    current_body = current.submobjects[0]
    assert any(isinstance(child, Circle) for child in voltage_body.submobjects)
    assert any(isinstance(child, Circle) for child in current_body.submobjects)
    assert any(isinstance(child, Text) and child.text == "V" for child in voltage_body.submobjects)
    assert any(isinstance(child, Text) and child.text == "A" for child in current_body.submobjects)
    assert voltage_body.get_all_points().shape != current_body.get_all_points().shape


def test_measurement_probe_layout_preserves_renderer_metadata() -> None:
    graph = CircuitGraph()
    current = CurrentProbe("ip1")
    voltage = VoltageProbe("vp1")
    graph.add(current)
    graph.add(voltage)
    graph.connect(current.port_out, voltage.port_pos)
    elements = {"ip1": current, "vp1": voltage}
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
