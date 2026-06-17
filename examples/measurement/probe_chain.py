"""
Measurement probe chain: inline current sense plus voltage sense to ground.

Preview: ``manim --disable_caching -pql examples/measurement/probe_chain.py MeasurementProbeScene``
"""

from __future__ import annotations

from manim_engineering.components import (
    CurrentProbe,
    Ground,
    InputDriver,
    Resistor,
    VoltageProbe,
)
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine, Point2D


def build_measurement_probe_fixture():
    """Return graph, elements, and layout for a basic measurement probe chain."""
    graph = CircuitGraph()
    source = InputDriver("src", label="IN")
    current = CurrentProbe("ip", label="I")
    resistor = Resistor("rs", label="Rsense")
    voltage = VoltageProbe("vp", label="Vload")
    ground = Ground("gnd", label="GND")

    for component in (source, current, resistor, voltage, ground):
        component.attach_to(graph)

    graph.connect(source.get_port("out"), current.port_in)
    graph.connect(current.port_out, resistor.get_port("a"))
    graph.connect(resistor.get_port("b"), ground.get_port("gnd"))
    graph.connect(voltage.port_pos, resistor.get_port("b"))
    graph.connect(voltage.port_neg, ground.get_port("gnd"))

    elements = {
        "src": source,
        "ip": current,
        "rs": resistor,
        "vp": voltage,
        "gnd": ground,
    }
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides={
            "src": Point2D(0.0, 0.0),
            "ip": Point2D(1.0, 0.0),
            "rs": Point2D(2.1, 0.0),
            "gnd": Point2D(3.4, -0.75),
            "vp": Point2D(3.1, 0.55),
        },
    )
    return graph, elements, layout


def main() -> None:
    graph, elements, layout = build_measurement_probe_fixture()
    print(f"measurement nodes={len(graph.nodes)} wires={len(layout.wires)}")
    print(f"components={list(elements)}")


if __name__ == "__main__":
    main()


MeasurementProbeScene = None


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

    class MeasurementProbeScene(TopologyTeachingScene):
        """Inline current and node-voltage measurement probes in one circuit."""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_measurement_probe_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "Measurement probes",
                "Current is sensed inline; voltage is sensed from the load node to ground.",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        MeasurementProbeScene = None
    else:
        msg = f"failed to import MeasurementProbeScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
