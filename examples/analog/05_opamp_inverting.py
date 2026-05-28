"""
运放反相放大器：Rin→OpAmp(-), Rf反馈, (+)接地, Vout = -Rf/Rin·Vin。

Preview: ``manim -pql examples/analog/05_opamp_inverting.py OpAmpInvertingScene``
"""

from __future__ import annotations

from manim_engineering.components import Ground, InputDriver, OpAmp, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.opamp import inverting_integrator_preset


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
    preset = inverting_integrator_preset(op1, rin, rf, in_drv, gnd)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


OpAmpInvertingScene = None

try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import TopologyFixture, TopologyTeachingScene

    class OpAmpInvertingScene(TopologyTeachingScene):
        """运放反相放大器：Vin→Rin→OP(-), Rf反馈, Av = -Rf/Rin。"""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_opamp_inverting_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "运放反相放大 · Av = -Rf/Rin",
                "虚地反相组态：输出与输入反相，增益由电阻比决定",
            )

except ImportError:
    OpAmpInvertingScene = None
