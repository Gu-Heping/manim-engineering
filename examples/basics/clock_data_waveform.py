"""
Digital clock + data: layout, circuit render, waveform panel, SignalFlow + WaveformSync.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, WaveformSync
from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer, WaveformPanelRenderer
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType
from manim_engineering.waveform import derive_bundle_from_signals


def build_fixture():
    """Return graph, elements, layout, clock/data signals, and derived waveform bundle."""
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    drv.attach_to(graph)
    rcv.attach_to(graph)
    graph.connect(drv.get_pin("b"), rcv.get_pin("a"))
    graph.connect(drv.get_pin("a"), rcv.get_pin("b"))

    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().layout(graph, elements)

    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.get_pin("b"), rcv.get_pin("a"), graph=graph)
    data.propagate(drv.get_pin("a"), rcv.get_pin("b"), graph=graph)

    bundle = derive_bundle_from_signals((clock, data))
    return graph, elements, layout, clock, data, bundle


def main() -> None:
    graph, elements, layout, clock, data, bundle = build_fixture()
    print(f"traces: {[t.signal_name for t in bundle.traces]}")
    print(f"clock end level: {bundle.trace_named('clk').samples[-1].level}")
    print(f"topology connections: {len(graph.connections)}")
    flow = SignalFlow(clock, layout=layout, graph=graph)
    sync = WaveformSync(
        bundle,
        (clock, data),
        panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
    )
    print(f"SignalFlow run_time={flow.build().run_time}s, sync beat={sync.resolved_beat()}")


if __name__ == "__main__":
    main()


try:
    from manim import Scene, VGroup

    class ClockDataWaveformDemo(Scene):
        """Circuit + waveform panel with propagation and timing sync."""

        def construct(self) -> None:
            graph, elements, layout, clock, data, bundle = build_fixture()
            circuit = MinimalRenderer().render_layout(layout, graph, elements)
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            self.add(VGroup(circuit, waveform_panel))

            SignalFlow(clock, layout=layout, graph=graph).play(self)
            WaveformSync(bundle, (clock, data), panel_spec=panel_spec).play(self)

except ImportError:
    pass
