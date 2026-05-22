"""
Two resistors: layout, render, propagate a digital edge, play SignalFlow.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType


def build_fixture():
    """Return graph, elements, layout, signal after one propagation step."""
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)

    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return graph, elements, layout, signal


def main() -> None:
    graph, elements, layout, signal = build_fixture()
    flow = SignalFlow(signal, layout=layout, graph=graph)
    plan = flow.build()
    print(
        f"SignalFlow plan: {len(plan.overlays)} overlay(s), "
        f"{len(plan.animations)} animation(s), run_time={plan.run_time}s"
    )
    print(f"topology connections: {len(graph.connections)}")


if __name__ == "__main__":
    main()


try:
    from manim import Scene

    class SignalFlowDemo(Scene):
        """Play propagation highlight along the routed net between R1 and R2."""

        def construct(self) -> None:
            graph, elements, layout, signal = build_fixture()
            scene_mob = MinimalRenderer().render_layout(layout, graph, elements)
            self.add(scene_mob)
            SignalFlow(signal, layout=layout, graph=graph).play(self)

except ImportError:
    pass
