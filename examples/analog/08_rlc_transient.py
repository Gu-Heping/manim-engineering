"""
RLC串联暂态响应：AC源→R→L→C→GND，二阶电路阻尼响应。

Preview: ``manim -pql examples/analog/08_rlc_transient.py RLCTransientScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import Capacitor, Ground, Inductor, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer


def build_rlc_transient_fixture():
    graph = CircuitGraph()
    src = InputDriver("src", label="AC", signal_type=SignalType.ANALOG)
    r1 = Resistor("r1", label="R")
    l1 = Inductor("l1", label="L")
    c1 = Capacitor("c1", label="C")
    gnd = Ground("gnd", label="GND")
    for comp in (src, r1, l1, c1, gnd):
        comp.attach_to(graph)
    graph.connect(src.get_pin("out"), r1.get_pin("a"))
    graph.connect(r1.get_pin("b"), l1.get_pin("a"))
    graph.connect(l1.get_pin("b"), c1.get_pin("a"))
    graph.connect(c1.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"src": src, "r1": r1, "l1": l1, "c1": c1, "gnd": gnd}
    layout = LayoutEngine().solve(graph, elements)
    return graph, elements, layout


class RLCTransientScene(Scene):
    """RLC串联暂态：AC源→R→L→C→GND，二阶系统阻尼响应。"""

    def construct(self) -> None:
        graph, elements, layout = build_rlc_transient_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("RLC串联暂态 · AC→R→L→C→GND", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
