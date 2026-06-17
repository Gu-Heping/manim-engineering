"""
Digital gate chain: two inputs fan out to AND/OR, then AND feeds an inverter.

Preview: ``manim --disable_caching -pql examples/digital/logic_gate_chain.py LogicGateChainScene``
"""

from __future__ import annotations

from manim_engineering.components import ANDGate, InputDriver, NOTGate, ORGate
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine, Point2D


def build_logic_gate_chain_fixture():
    """Return graph, elements, and layout for a basic digital gate chain."""
    graph = CircuitGraph()
    in_a = InputDriver("in_a", label="A", signal_type=SignalType.DIGITAL)
    in_b = InputDriver("in_b", label="B", signal_type=SignalType.DIGITAL)
    and_gate = ANDGate("and1", label="AND")
    or_gate = ORGate("or1", label="OR")
    inverter = NOTGate("not1", label="NOT")

    for component in (in_a, in_b, and_gate, or_gate, inverter):
        component.attach_to(graph)

    graph.connect(in_a.get_pin("out"), and_gate.port_a)
    graph.connect(in_b.get_pin("out"), and_gate.port_b)
    graph.connect(in_a.get_pin("out"), or_gate.port_a)
    graph.connect(in_b.get_pin("out"), or_gate.port_b)
    graph.connect(and_gate.port_out, inverter.port_in)

    elements = {
        "in_a": in_a,
        "in_b": in_b,
        "and1": and_gate,
        "or1": or_gate,
        "not1": inverter,
    }
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides={
            "in_a": Point2D(0.0, 0.65),
            "in_b": Point2D(0.0, -0.05),
            "and1": Point2D(1.0, 0.30),
            "or1": Point2D(1.0, -0.75),
            "not1": Point2D(2.40, 0.35),
        },
    )
    return graph, elements, layout


def main() -> None:
    graph, elements, layout = build_logic_gate_chain_fixture()
    print(f"digital nodes={len(graph.nodes)} wires={len(layout.wires)}")
    print(f"components={list(elements)}")


if __name__ == "__main__":
    main()


LogicGateChainScene = None


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

    class LogicGateChainScene(TopologyTeachingScene):
        """A/B fanout into logic gates, with AND output inverted."""

        subtitle_band = 0.8

        def build_fixture(self) -> TopologyFixture:
            graph, elements, layout = build_logic_gate_chain_fixture()
            return TopologyFixture(graph=graph, elements=elements, layout=layout)

        def hud_texts(self, _fixture: TopologyFixture) -> tuple[str, str]:
            return (
                "Digital logic gates",
                "Inputs A and B fan out to AND/OR; AND then drives an inverter.",
            )

except ImportError as exc:
    if _is_optional_scene_import_error(exc):
        LogicGateChainScene = None
    else:
        msg = f"failed to import LogicGateChainScene from {__file__}: {exc}"
        raise ImportError(msg) from exc
