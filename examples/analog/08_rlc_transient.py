"""
RLC串联暂态响应：AC源→R→L→C→GND，二阶电路阻尼响应。

Preview: ``manim -pql examples/analog/08_rlc_transient.py RLCTransientScene``
"""

from __future__ import annotations

from manim_engineering.components import Capacitor, Ground, Inductor, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine


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


RLCTransientScene = None


def _is_optional_scene_import_error(exc: ImportError) -> bool:
    name = getattr(exc, "name", None)
    if not name:
        return False
    return name == "manim" or str(name).startswith("manim.")

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

    class RLCTransientScene(TopologyTeachingScene):
        """RLC串联暂态：AC源→R→L→C→GND，二阶系统阻尼响应。"""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_rlc_transient_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "RLC串联暂态 · AC→R→L→C→GND",
                "二阶 RLC 回路：电阻、电感、电容共同决定暂态与谐振",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        RLCTransientScene = None
    else:
        msg = f"failed to import RLCTransientScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
