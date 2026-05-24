"""
半波整流演示：交流信号源 → Diode → R负载 → GND。

Preview: ``manim -pql examples/analog/02_diode_rectifier.py HalfWaveRectifierScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import Diode, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer


def build_rectifier_fixture():
    graph = CircuitGraph()
    src = InputDriver("src", label="AC", signal_type=SignalType.ANALOG)
    d1 = Diode("d1", label="D1")
    rl = Resistor("rl", label="RL")
    gnd = Ground("gnd", label="GND")
    for comp in (src, d1, rl, gnd):
        comp.attach_to(graph)
    graph.connect(src.get_pin("out"), d1.get_pin("anode"))
    graph.connect(d1.get_pin("cathode"), rl.get_pin("a"))
    graph.connect(rl.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"src": src, "d1": d1, "rl": rl, "gnd": gnd}
    layout = LayoutEngine().solve(graph, elements)
    return graph, elements, layout


class HalfWaveRectifierScene(Scene):
    """半波整流：交流源 → 二极管 → 负载电阻 → 地。"""

    def construct(self) -> None:
        graph, elements, layout = build_rectifier_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("半波整流 · AC→D1→RL→GND", role="title")
        title.to_edge(UP, buff=0.3)
        self.add(title)
        self.wait(2)
