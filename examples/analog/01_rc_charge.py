"""
RC充电演示：InputDriver → R1 → C1 → GND。

Preview: ``manim -pql examples/analog/01_rc_charge.py RCChargeScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import Capacitor, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer


def build_rc_charge_fixture():
    graph = CircuitGraph()
    drv = InputDriver("drv", label="IN", signal_type=SignalType.DIGITAL)
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    gnd = Ground("gnd", label="GND")
    for comp in (drv, r1, c1, gnd):
        comp.attach_to(graph)
    graph.connect(drv.get_pin("out"), r1.get_pin("a"))
    graph.connect(r1.get_pin("b"), c1.get_pin("a"))
    graph.connect(c1.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"drv": drv, "r1": r1, "c1": c1, "gnd": gnd}
    layout = LayoutEngine().solve(graph, elements)
    return graph, elements, layout


class RCChargeScene(Scene):
    """RC充电回路：信号源 → 电阻 → 电容 → 地，三元件串联。"""

    def construct(self) -> None:
        graph, elements, layout = build_rc_charge_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("RC充电回路 · IN→R1→C1→GND", role="title")
        title.to_edge(UP, buff=0.3)
        self.add(title)
        self.wait(2)
