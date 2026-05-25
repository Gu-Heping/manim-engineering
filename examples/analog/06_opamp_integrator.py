"""
运放积分电路：Rin→OpAmp(-), C反馈, (+)接地, Vout = -1/(RC)∫Vin dt。

Preview: ``manim -pql examples/analog/06_opamp_integrator.py OpAmpIntegratorScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import Capacitor, Ground, InputDriver, OpAmp, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.opamp import inverting_integrator_preset
from manim_engineering.renderers.minimal import ManimRenderer


def build_opamp_integrator_fixture():
    graph = CircuitGraph()
    op1 = OpAmp("op1", label="A1")
    rin = Resistor("rin1", label="Rin")
    cf = Capacitor("cf1", label="Cf")
    in_drv = InputDriver("in_drv", label="Vin", signal_type=SignalType.ANALOG)
    gnd = Ground("gnd1", label="GND")
    for comp in (op1, rin, cf, in_drv, gnd):
        comp.attach_to(graph)
    graph.connect(in_drv.get_pin("out"), rin.get_pin("a"))
    graph.connect(rin.get_pin("b"), op1.get_pin("in_n"))
    graph.connect(op1.get_pin("in_p"), gnd.get_pin("gnd"))
    graph.connect(rin.get_pin("b"), cf.get_pin("a"))
    graph.connect(cf.get_pin("b"), op1.get_pin("out"))
    elements = {"op1": op1, "rin1": rin, "cf1": cf, "in_drv": in_drv, "gnd1": gnd}
    preset = inverting_integrator_preset(op1, rin, cf, in_drv, gnd)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


class OpAmpIntegratorScene(Scene):
    """运放积分电路：Vin→Rin→OP(-), Cf反馈, Vout = -1/(RC)∫Vin dt。"""

    def construct(self) -> None:
        graph, elements, layout = build_opamp_integrator_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("运放积分器 · Vout = -1/RC ∫ Vin dt", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
