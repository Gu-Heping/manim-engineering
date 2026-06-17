"""
齐纳稳压电路：VCC→Rs→ZenerD(反偏)→GND，负载RL并联在齐纳两端。

Preview: ``manim --disable_caching -pql examples/analog/07_zener_regulator.py ZenerRegulatorScene``
"""

from __future__ import annotations

from manim_engineering.components import VCC, Ground, Resistor, ZenerDiode
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.zener_regulator import zener_regulator_preset


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


ZenerRegulatorScene = None


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

    class ZenerRegulatorScene(TopologyTeachingScene):
        """齐纳稳压：VCC→Rs→Dz(反偏)→GND，RL并联稳压。"""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_zener_regulator_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "齐纳稳压 · VCC→Rs→Dz‖RL→GND",
                "齐纳二极管反偏击穿，在负载两端维持近似恒定电压",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        ZenerRegulatorScene = None
    else:
        msg = f"failed to import ZenerRegulatorScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
