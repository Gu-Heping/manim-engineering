"""
Three-layer acceptance: core graph → layout.solve → ManimRenderer + SignalFlow.

R1–C1 passive chain wired via port API. One digital edge propagates along the routed net.

Preview: ``manim -pql examples/basics/acceptance_three_layer.py AcceptanceScene``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Capacitor, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal, SignalType


def build_fixture():
    """Return circuit, elements, layout, and a signal with one propagation step."""
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    circuit.add(r1)
    circuit.add(c1)
    circuit.connect(r1.port_b, c1.port_a)

    elements = {"r1": r1, "c1": c1}
    layout = LayoutEngine().solve(circuit, elements)

    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.port_b, c1.port_a, graph=circuit)
    return circuit, elements, layout, signal


def main() -> None:
    circuit, elements, layout, signal = build_fixture()
    flow = SignalFlow(signal, layout=layout, graph=circuit)
    plan = flow.build()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(
        f"SignalFlow: {len(plan.overlays)} overlay(s), "
        f"run_time={plan.run_time}s"
    )


if __name__ == "__main__":
    main()


try:
    from manim import Scene, config

    class AcceptanceScene(Scene):
        """Show R1–C1 layout, pause, then play propagation along the net."""

        def construct(self) -> None:
            circuit, elements, layout, signal = build_fixture()
            config.frame_width = max(4.0, layout.layout_bbox.width + 1.0)
            config.frame_height = max(2.0, layout.layout_bbox.height + 1.0)
            circuit_mob = ManimRenderer().render(circuit, layout, elements)
            self.add(circuit_mob)
            self.wait(1.5)
            SignalFlow(
                signal,
                layout=layout,
                graph=circuit,
                duration=1.2,
            ).play(self)
            self.wait(2.0)

except ImportError:
    pass
