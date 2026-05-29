"""
半波整流演示：交流信号源 → Diode → R负载 → GND。

Preview: ``manim -pql examples/analog/02_diode_rectifier.py HalfWaveRectifierScene``
"""

from __future__ import annotations

from manim_engineering.components import Diode, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine


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


def main() -> None:
    graph, elements, layout = build_rectifier_fixture()
    print(f"nodes={len(graph.nodes)} wires={len(layout.wires)}")


if __name__ == "__main__":
    main()


HalfWaveRectifierScene = None

try:
    import importlib.util
    from pathlib import Path

    _SHARED_PATH = Path(__file__).resolve().parents[1] / "_shared.py"
    _SHARED_SPEC = importlib.util.spec_from_file_location("me_examples_shared", _SHARED_PATH)
    assert _SHARED_SPEC is not None and _SHARED_SPEC.loader is not None
    _shared = importlib.util.module_from_spec(_SHARED_SPEC)
    _SHARED_SPEC.loader.exec_module(_shared)
    TopologyFixture = _shared.TopologyFixture
    TopologyTeachingScene = _shared.TopologyTeachingScene

    class HalfWaveRectifierScene(TopologyTeachingScene):
        """半波整流：交流源 → 二极管 → 负载电阻 → 地。"""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_rectifier_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "半波整流 · AC→D1→RL→GND",
                "交流源经二极管半波整流，负载电阻上得到脉动直流",
            )

except ImportError:
    HalfWaveRectifierScene = None
