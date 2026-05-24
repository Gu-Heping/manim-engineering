"""
NPN共发射极放大器：VCC→Rc→NPN集电极，NPN发射极→Re→GND, 基极输入。

Preview: ``manim -pql examples/analog/04_npn_amplifier.py NPNAmplifierScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import NPN, VCC, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import Point2D
from manim_engineering.renderers.minimal import ManimRenderer

AMP_OVERRIDES: dict[str, Point2D] = {
    "vcc1": Point2D(0.5, 2.5),
    "rc1": Point2D(-1.5, 1.8),
    "q1": Point2D(-1.0, 0.5),
    "re1": Point2D(-1.5, -0.9),
    "gnd1": Point2D(0.5, -1.7),
    "in_drv": Point2D(-3.5, 0.8),
}


def build_npn_amplifier_fixture():
    graph = CircuitGraph()
    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    rc = Resistor("rc1", label="Rc")
    re = Resistor("re1", label="Re")
    q1 = NPN("q1", label="Q1")
    in_drv = InputDriver("in_drv", label="IN", signal_type=SignalType.ANALOG)
    for comp in (vcc, gnd, rc, re, q1, in_drv):
        comp.attach_to(graph)
    graph.connect(vcc.get_pin("vcc"), rc.get_pin("a"))
    graph.connect(rc.get_pin("b"), q1.get_pin("collector"))
    graph.connect(q1.get_pin("emitter"), re.get_pin("a"))
    graph.connect(re.get_pin("b"), gnd.get_pin("gnd"))
    graph.connect(in_drv.get_pin("out"), q1.get_pin("base"))
    elements = {"vcc1": vcc, "gnd1": gnd, "rc1": rc, "re1": re, "q1": q1, "in_drv": in_drv}
    layout = LayoutEngine().layout(graph, elements, placement_overrides=AMP_OVERRIDES)
    return graph, elements, layout


class NPNAmplifierScene(Scene):
    """NPN共发射极放大电路：VCC→Rc→Q1→Re→GND，基极输入IN。"""

    def construct(self) -> None:
        graph, elements, layout = build_npn_amplifier_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=1.0)
        title = subtitle_text("NPN共发放大器 · VCC→Rc→Q1→Re→GND", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
