"""
运放反相放大器：Rin→OpAmp(-), Rf反馈, (+)接地, Vout = -Rf/Rin·Vin。

Preview: ``manim -pql examples/analog/05_opamp_inverting.py OpAmpInvertingScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import Ground, InputDriver, OpAmp, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import Point2D
from manim_engineering.renderers.minimal import ManimRenderer

OPAMP_OVERRIDES: dict[str, Point2D] = {
    "op1": Point2D(0.0, 0.0),
    "rin1": Point2D(-2.5, 0.75),
    "rf1": Point2D(-0.2, 1.5),
    "in_drv": Point2D(-4.5, 0.75),
    "gnd1": Point2D(-1.8, -0.6),
}


def build_opamp_inverting_fixture():
    graph = CircuitGraph()
    op1 = OpAmp("op1", label="A1")
    rin = Resistor("rin1", label="Rin")
    rf = Resistor("rf1", label="Rf")
    in_drv = InputDriver("in_drv", label="Vin", signal_type=SignalType.ANALOG)
    gnd = Ground("gnd1", label="GND")
    for comp in (op1, rin, rf, in_drv, gnd):
        comp.attach_to(graph)
    graph.connect(in_drv.get_pin("out"), rin.get_pin("a"))
    graph.connect(rin.get_pin("b"), op1.get_pin("in_n"))
    graph.connect(op1.get_pin("in_p"), gnd.get_pin("gnd"))
    graph.connect(rin.get_pin("b"), rf.get_pin("a"))
    graph.connect(rf.get_pin("b"), op1.get_pin("out"))
    elements = {"op1": op1, "rin1": rin, "rf1": rf, "in_drv": in_drv, "gnd1": gnd}
    layout = LayoutEngine().layout(graph, elements, placement_overrides=OPAMP_OVERRIDES)
    return graph, elements, layout


class OpAmpInvertingScene(Scene):
    """运放反相放大器：Vin→Rin→OP(-), Rf反馈, Av = -Rf/Rin。"""

    def construct(self) -> None:
        graph, elements, layout = build_opamp_inverting_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("运放反相放大 · Av = -Rf/Rin", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
