"""MinimalRenderer.render_circuit composes graph + layout."""

from __future__ import annotations

import numpy as np
import pytest
from manim import Dot

pytest.importorskip("manim")

from manim_engineering.components import VCC, Ground, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine, Point2D
from manim_engineering.renderers.minimal import MinimalRenderer, theme


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


def test_render_layout_adds_crossing_mask_for_non_junction_wire_crossing() -> None:
    circuit = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    vcc = VCC("vcc")
    gnd = Ground("gnd")
    for element in (r1, r2, vcc, gnd):
        element.attach_to(circuit)

    circuit.connect(r1.get_port("b"), r2.get_port("a"))
    circuit.connect(vcc.get_port("vcc"), gnd.get_port("gnd"))
    elements = {"r1": r1, "r2": r2, "vcc": vcc, "gnd": gnd}
    layout = LayoutEngine().layout(
        circuit,
        elements,
        placement_overrides={
            "r1": Point2D(0.0, 0.0),
            "r2": Point2D(2.0, 0.0),
            "vcc": Point2D(1.4, -1.2),
            "gnd": Point2D(1.4, 1.0),
        },
    )

    rendered = MinimalRenderer().render_layout(layout, circuit, elements)
    top_level_dots = [mob for mob in rendered.submobjects if isinstance(mob, Dot)]

    assert any(issue.kind == "crossing_without_junction" for issue in layout.routing_report.issues)
    assert len(top_level_dots) == 1
    assert top_level_dots[0].get_color().to_hex().lower() == theme.INTERFACE_PANEL_FILL
