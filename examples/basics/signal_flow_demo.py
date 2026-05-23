"""
Two resistors: layout, render, propagate a digital edge, play SignalFlow.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo``
"""

from __future__ import annotations

from manim_engineering.animation import BEAT_DURATION, INTRO_PAUSE, play_propagation_beat
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.semantic import LogicLevel, LogicState, Signal


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
    print(f"beat_duration={BEAT_DURATION}s")
    print(f"topology connections: {len(graph.connections)}")


if __name__ == "__main__":
    main()


try:
    from manim import Scene

    class SignalFlowDemo(Scene):
        """Play propagation highlight along the routed net between R1 and R2."""

        def construct(self) -> None:
            graph, elements, layout, signal = build_fixture()
            topology = ManimRenderer().render_topology(graph, layout, elements)
            self.add(topology.circuit_group)
            self.wait(INTRO_PAUSE)
            play_propagation_beat(
                self,
                signal,
                layout=layout,
                graph=graph,
                duration=BEAT_DURATION,
            )

except ImportError:
    pass
