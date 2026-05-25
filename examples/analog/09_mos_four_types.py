"""
MOSFET 四型符号对照：增强/耗尽 × N/P。

Preview: ``manim -pql examples/analog/09_mos_four_types.py MosFourTypesScene``
"""

from __future__ import annotations

from manim import UP, Scene

from manim_engineering.animation import configure_topology_scene_camera, subtitle_text
from manim_engineering.components import NMOS, NMOSDepletion, PMOS, PMOSDepletion
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


class MosFourTypesScene(Scene):
    """增强 vs 耗尽、N vs P 四型 MOSFET 符号对照（默认 textbook_vertical 四端子画法）。"""

    def construct(self) -> None:
        graph, elements, layout = build_mos_four_types_fixture()
        renderer = ManimRenderer()
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text(
            "MOSFET 四型 · 增强(沟道断) / 耗尽(沟道通) · N / P",
            role="title",
        )
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)


class MosFourTypesArrowOnChannelScene(MosFourTypesScene):
    """同一四型网格，使用 arrow_on_channel 画法对比。"""

    def construct(self) -> None:
        graph, elements, layout = build_mos_four_types_fixture()
        renderer = ManimRenderer(mosfet_convention=MosfetSymbolConvention.arrow_on_channel)
        mobject = renderer.render_circuit(graph, layout, elements)
        self.add(mobject)
        configure_topology_scene_camera(self, layout, subtitle_band=0.8)
        title = subtitle_text(
            "MOSFET 四型 · arrow_on_channel 画法",
            role="title",
        )
        title.to_edge(UP, buff=0.2)
        self.add(title)
        self.wait(2)
