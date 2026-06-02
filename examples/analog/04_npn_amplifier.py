"""
NPN共发射极放大器：VCC→Rc→NPN集电极，NPN发射极→Re→GND, 基极输入。

Preview: ``manim -pql examples/analog/04_npn_amplifier.py NPNAmplifierScene``
"""

from __future__ import annotations

from manim_engineering.components import NPN, VCC, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.npn_ce import common_emitter_preset


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
    preset = common_emitter_preset(vcc, gnd, rc, re, q1, in_drv)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


NPNAmplifierScene = None


def _is_optional_scene_import_error(exc: ImportError) -> bool:
    name = getattr(exc, "name", None)
    if not name:
        return False
    return name == "manim" or str(name).startswith("manim.")

try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import TopologyFixture, TopologyTeachingScene

    class NPNAmplifierScene(TopologyTeachingScene):
        """NPN共发射极放大电路：VCC→Rc→Q1→Re→GND，基极输入IN。"""

        subtitle_band = 1.0

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_npn_amplifier_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "NPN共发放大器 · VCC→Rc→Q1→Re→GND",
                "共发射极组态：基极小信号控制集电极电流",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        NPNAmplifierScene = None
    else:
        msg = f"failed to import NPNAmplifierScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
