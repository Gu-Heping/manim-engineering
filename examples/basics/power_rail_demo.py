"""
Three resistors in a chain: layout, render, dual signal propagation, waveform.

Clean demo using only Resistor components (fully tested symbol rendering).
Signals propagate through the chain with animated highlights and waveform sync.

Preview: ``manim -pql examples/basics/power_rail_demo.py PowerRailDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, WaveformSync
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer, WaveformPanelRenderer
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType
from manim_engineering.waveform import derive_bundle_from_signals, scene_frame_bounds


def build_fixture():
    graph = CircuitGraph()
    r1 = Resistor("res_a", label="R1")
    r2 = Resistor("res_b", label="R2")
    r3 = Resistor("res_c", label="R3")
    for comp in (r1, r2, r3):
        comp.attach_to(graph)

    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    graph.connect(r2.get_pin("b"), r3.get_pin("a"))

    elements = {"res_a": r1, "res_b": r2, "res_c": r3}
    layout = LayoutEngine().layout(graph, elements)

    clk = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clk.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    data.propagate(r2.get_pin("b"), r3.get_pin("a"), graph=graph)

    bundle = derive_bundle_from_signals((clk, data))
    return graph, elements, layout, clk, data, bundle


def main() -> None:
    graph, elements, layout, clk, data, bundle = build_fixture()
    print(f"components: {list(elements.keys())}")
    print(f"connections: {len(graph.connections)}")
    print(f"traces: {['clk', 'data']}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    flow = SignalFlow(clk, layout=layout, graph=graph)
    print(f"SignalFlow plan: {flow.build().run_time}s")


if __name__ == "__main__":
    main()


try:
    from manim import Scene, VGroup, config

    class PowerRailDemo(Scene):
        """Three-resistor chain with signal propagation and waveform sync."""

        def construct(self) -> None:
            graph, elements, layout, clk, data, bundle = build_fixture()

            circuit = MinimalRenderer().render_layout(layout, graph, elements)
            n_placed = len(layout.placements)
            components = VGroup(*circuit.submobjects[:n_placed])
            wires = VGroup(*circuit.submobjects[n_placed:])
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            frame_w, frame_h = scene_frame_bounds(
                layout, panel_spec, trace_count=len(bundle.traces)
            )
            config.frame_width = max(6.0, frame_w)
            config.frame_height = max(3.0, frame_h)
            self.add(components, wires, waveform_panel)

            SignalFlow(clk, layout=layout, graph=graph).play(self)
            WaveformSync(bundle, (clk, data), panel_spec=panel_spec).play(self)

except ImportError:
    pass
