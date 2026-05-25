"""
齐纳稳压电路：VCC→Rs→ZenerD(反偏)→GND，负载RL并联在齐纳两端。

Preview: ``manim -pql examples/analog/07_zener_regulator.py ZenerRegulatorScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import VCC, Ground, Resistor, ZenerDiode
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.zener_regulator import zener_regulator_preset
from manim_engineering.renderers.minimal import ManimRenderer


def build_zener_regulator_fixture():
    graph = CircuitGraph()
    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    rs = Resistor("rs1", label="Rs")
    zd = ZenerDiode("zd1", label="Dz")
    rl = Resistor("rl1", label="RL")
    for comp in (vcc, gnd, rs, zd, rl):
        comp.attach_to(graph)
    graph.connect(vcc.get_pin("vcc"), rs.get_pin("a"))
    graph.connect(rs.get_pin("b"), zd.get_pin("cathode"))
    graph.connect(zd.get_pin("anode"), gnd.get_pin("gnd"))
    graph.connect(rs.get_pin("b"), rl.get_pin("a"))
    graph.connect(rl.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"vcc1": vcc, "gnd1": gnd, "rs1": rs, "zd1": zd, "rl1": rl}
    preset = zener_regulator_preset(vcc, gnd, rs, zd, rl)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


class ZenerRegulatorScene(Scene):
    """齐纳稳压：VCC→Rs→Dz(反偏)→GND，RL并联稳压。"""

    def construct(self) -> None:
        graph, elements, layout = build_zener_regulator_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text("齐纳稳压 · VCC→Rs→Dz‖RL→GND", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
