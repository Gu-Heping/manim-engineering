"""
IEC resistor renderer: same semantic circuit, IEC visual family selected externally.

Preview: ``manim --disable_caching -pql examples/renderers/iec_resistor.py IECResistorScene``
"""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine, Point2D


def build_iec_resistor_fixture():
    """Return graph, elements, and layout for a two-resistor IEC renderer demo."""
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    for component in (r1, r2):
        component.attach_to(graph)
    graph.connect(r1.port_b, r2.port_a)

    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides={
            "r1": Point2D(0.0, 0.0),
            "r2": Point2D(1.25, 0.0),
        },
    )
    return graph, elements, layout


def main() -> None:
    graph, elements, layout = build_iec_resistor_fixture()
    print(f"iec-renderer nodes={len(graph.nodes)} wires={len(layout.wires)}")
    print(f"components={list(elements)}")


if __name__ == "__main__":
    main()


IECResistorScene = None


def _is_optional_scene_import_error(exc: ImportError) -> bool:
    name = getattr(exc, "name", None)
    if not name:
        return False
    return name == "manim" or str(name).startswith("manim.")


try:
    import importlib.util
    from pathlib import Path

    from manim_engineering.renderers import IECManimRenderer

    _SHARED_PATH = Path(__file__).resolve().parents[1] / "_shared.py"
    _SHARED_SPEC = importlib.util.spec_from_file_location("me_examples_shared", _SHARED_PATH)
    assert _SHARED_SPEC is not None and _SHARED_SPEC.loader is not None
    _shared = importlib.util.module_from_spec(_SHARED_SPEC)
    _SHARED_SPEC.loader.exec_module(_shared)
    TopologyFixture = _shared.TopologyFixture
    TopologyTeachingScene = _shared.TopologyTeachingScene

    class IECResistorScene(TopologyTeachingScene):
        """Two-resistor circuit rendered with the IEC visual family."""

        subtitle_band = 0.75

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_iec_resistor_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def render_topology(self, fixture: TopologyFixture):
            return IECManimRenderer().render_topology(
                fixture.graph,
                fixture.layout,
                dict(fixture.elements),
            )

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "IEC renderer",
                "The semantic circuit stays unchanged; only the renderer family changes.",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        IECResistorScene = None
    else:
        msg = f"failed to import IECResistorScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
