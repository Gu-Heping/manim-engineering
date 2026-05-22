"""
Governance acceptance: R1–C1 layout, wires vs waveform band, SignalFlow.

Combines ``acceptance_three_layer`` (port API, ``LayoutEngine.solve``, ``ManimRenderer``)
with waveform panel placement below routed nets (``scene_frame_bounds``).

Preview: ``manim -pql examples/basics/governance_acceptance.py GovernanceAcceptanceScene``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Capacitor, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal, SignalType
from manim_engineering.waveform import derive_bundle_from_signals, scene_frame_bounds


def build_fixture():
    """Return circuit, elements, layout, propagated edge signal, and waveform bundle."""
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    circuit.add(r1)
    circuit.add(c1)
    circuit.connect(r1.port_b, c1.port_a)

    elements = {"r1": r1, "c1": c1}
    layout = LayoutEngine().solve(circuit, elements)

    edge = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    edge.propagate(r1.port_b, c1.port_a, graph=circuit)
    bundle = derive_bundle_from_signals((edge,))
    return circuit, elements, layout, edge, bundle


def main() -> None:
    circuit, elements, layout, edge, bundle = build_fixture()
    flow = SignalFlow(edge, layout=layout, graph=circuit)
    plan = flow.build()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(f"scene_bbox height: {layout.scene_bbox.height:.2f}")
    print(f"traces: {[t.signal_name for t in bundle.traces]}")
    print(
        f"SignalFlow: {len(plan.overlays)} overlay(s), "
        f"run_time={plan.run_time}s"
    )


if __name__ == "__main__":
    main()


try:
    from manim import Scene, VGroup, config

    class GovernanceAcceptanceScene(Scene):
        """R1–C1 circuit, waveform panel under wires, one propagation beat."""

        def construct(self) -> None:
            circuit, elements, layout, edge, bundle = build_fixture()
            circuit_mob = ManimRenderer().render(circuit, layout, elements)
            n_placed = len(layout.placements)
            components = VGroup(*circuit_mob.submobjects[:n_placed])
            wires = VGroup(*circuit_mob.submobjects[n_placed:])
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            frame_w, frame_h = scene_frame_bounds(
                layout, panel_spec, trace_count=len(bundle.traces)
            )
            config.frame_width = max(4.0, frame_w)
            config.frame_height = max(2.5, frame_h)
            # Z-order: components → wires → waveform panel.
            self.add(components, wires, waveform_panel)
            self.wait(3.0)
            SignalFlow(edge, layout=layout, graph=circuit, duration=2.5).play(self)
            self.wait(4.0)

except ImportError:
    pass
