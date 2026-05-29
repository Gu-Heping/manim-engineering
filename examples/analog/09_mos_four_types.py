"""
MOSFET 四型符号对照：增强/耗尽 × N/P。

Preview: ``manim -pql examples/analog/09_mos_four_types.py MosFourTypesScene``
"""

from __future__ import annotations

from manim_engineering.components import NMOS, PMOS, NMOSDepletion, PMOSDepletion
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import Point2D
from manim_engineering.renderers.minimal import ManimRenderer, MosfetSymbolConvention


def _four_type_overrides() -> dict[str, Point2D]:
    """2×2 grid: top row N/P enhancement, bottom row N/P depletion."""
    cell = 1.8
    return {
        "n_enh": Point2D(0.0, cell),
        "p_enh": Point2D(cell, cell),
        "n_dep": Point2D(0.0, 0.0),
        "p_dep": Point2D(cell, 0.0),
    }


def build_mos_four_types_fixture():
    graph = CircuitGraph()
    n_enh = NMOS("n_enh", label="NMOS")
    p_enh = PMOS("p_enh", label="PMOS")
    n_dep = NMOSDepletion("n_dep", label="N-DEP")
    p_dep = PMOSDepletion("p_dep", label="P-DEP")
    for comp in (n_enh, p_enh, n_dep, p_dep):
        comp.attach_to(graph)
    for comp in (n_enh, p_enh, n_dep, p_dep):
        graph.connect(comp.get_pin("bulk"), comp.get_pin("source"))
    elements = {
        "n_enh": n_enh,
        "p_enh": p_enh,
        "n_dep": n_dep,
        "p_dep": p_dep,
    }
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides=_four_type_overrides(),
    )
    return graph, elements, layout


MosFourTypesScene = None
MosFourTypesArrowOnChannelScene = None

try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import TopologyFixture, TopologyTeachingScene

    class MosFourTypesScene(TopologyTeachingScene):
        """增强 vs 耗尽、N vs P 四型 MOSFET 符号对照（textbook_vertical）。"""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_mos_four_types_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "MOSFET 四型 · 增强(沟道断) / 耗尽(沟道通) · N / P",
                "四型符号对照：增强型默认沟道断开，耗尽型默认沟道导通",
            )

    class MosFourTypesArrowOnChannelScene(MosFourTypesScene):
        """同一四型网格，使用 arrow_on_channel 画法对比。"""

        def render_topology(self, fixture: TopologyFixture):
            renderer = ManimRenderer(
                mosfet_convention=MosfetSymbolConvention.arrow_on_channel
            )
            return renderer.render_topology(
                fixture.graph,
                fixture.layout,
                dict(fixture.elements),
            )

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "MOSFET 四型 · arrow_on_channel 画法",
                "沟道箭头画法与 textbook_vertical 四端子符号对照",
            )

except ImportError:
    MosFourTypesScene = None
    MosFourTypesArrowOnChannelScene = None
