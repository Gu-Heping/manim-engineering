"""
CMOS反相器演示：VCC → PMOS → OUT → NMOS → GND, IN驱动两管栅极。

Preview: ``manim -pql examples/analog/03_cmos_inverter.py CMOSInverterScene``
"""

from __future__ import annotations

from manim import UP, Line, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import NMOS, PMOS, VCC, Ground, InputDriver
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.cmos_inverter import DRAIN_Y, OUT_X, cmos_inverter_preset
from manim_engineering.renderers.minimal import ManimRenderer, theme
from manim_engineering.renderers.minimal.labels import label_text

OUT_LABEL_POS = (0.8, DRAIN_Y)


def build_inverter_fixture():
    graph = CircuitGraph()
    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    pmos = PMOS("pm1", label="P1")
    nmos = NMOS("nm1", label="N1")
    in_drv = InputDriver("in_drv", label="IN", signal_type=SignalType.DIGITAL)
    for comp in (vcc, gnd, pmos, nmos, in_drv):
        comp.attach_to(graph)
    graph.connect(vcc.get_pin("vcc"), pmos.get_pin("source"))
    graph.connect(pmos.get_pin("drain"), nmos.get_pin("drain"))
    graph.connect(pmos.get_pin("bulk"), pmos.get_pin("source"))
    graph.connect(nmos.get_pin("source"), gnd.get_pin("gnd"))
    graph.connect(nmos.get_pin("bulk"), nmos.get_pin("source"))
    graph.connect(in_drv.get_pin("out"), pmos.get_pin("gate"))
    graph.connect(in_drv.get_pin("out"), nmos.get_pin("gate"))
    elements = {"vcc1": vcc, "gnd1": gnd, "pm1": pmos, "nm1": nmos, "in_drv": in_drv}
    preset = cmos_inverter_preset(vcc, gnd, pmos, nmos, in_drv)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


class CMOSInverterScene(Scene):
    """CMOS反相器：VCC→P1→OUT→N1→GND，IN驱动P1和N1栅极。"""

    def construct(self) -> None:
        graph, elements, layout = build_inverter_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=1.2)
        title = subtitle_text("CMOS Inverter · VCC→P1→OUT→N1→GND", role="title")
        title.to_edge(UP, buff=0.2)
        self.add(title)
        out_label = label_text("OUT", font_size=20, color="white")
        out_label.move_to([OUT_LABEL_POS[0], OUT_LABEL_POS[1], 0])
        out_wire = Line(
            [OUT_X, DRAIN_Y, 0.0],
            [OUT_LABEL_POS[0] - 0.12, DRAIN_Y, 0.0],
            stroke_color=theme.color_for_signal_type(SignalType.ANALOG),
            stroke_width=theme.WIRE_STROKE_WIDTH,
        )
        self.add(out_wire, out_label)
        self.wait(2)
