"""
Digital clock + data: layout, circuit render, waveform panel, SignalFlow + WaveformSync.

Two-component bus (DRV/RCV) with clock and data traces in a panel below routed wires.
Demonstrates circuit/waveform separation and z-order after layout/render fixes.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo``
Acceptance render: ``manim -qm examples/basics/clock_data_waveform.py ClockDataWaveformDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, WaveformSync
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal, SignalType
from manim_engineering.waveform import derive_bundle_from_signals, scene_frame_bounds


def build_fixture():
    """Return graph, elements, layout, clock/data signals, and derived waveform bundle."""
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    graph.add(drv)
    graph.add(rcv)
    graph.connect(drv.port_b, rcv.port_a)
    graph.connect(drv.port_a, rcv.port_b)

    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().solve(graph, elements)

    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.port_b, rcv.port_a, graph=graph)
    data.propagate(drv.port_a, rcv.port_b, graph=graph)

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
    from pathlib import Path

    from manim import Scene, VGroup, config
    from PIL import Image

    _ACCEPTANCE_MEDIA = Path("media/videos/clock_data_waveform")

    def _save_camera_frame(scene: Scene, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = scene.camera.get_image()
        if hasattr(frame, "save"):
            frame.save(path)
        else:
            import numpy as np

            Image.fromarray(np.asarray(frame)).save(path)

    class ClockDataWaveformDemo(Scene):
        """DRV–RCV circuit, waveform panel under wires, propagation + timing sync."""

        def construct(self) -> None:
            graph, elements, layout, clock, data, bundle = build_fixture()
            topology = ManimRenderer().render_topology(graph, layout, elements)
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            content = VGroup(topology.components, topology.wires, waveform_panel)
            self.add(content)

            frame_w, frame_h = scene_frame_bounds(
                layout,
                panel_spec,
                trace_count=len(bundle.traces),
                target_fill=0.70,
            )
            config.frame_width = max(4.0, frame_w)
            config.frame_height = max(2.5, frame_h)
            self.camera.frame_width = config.frame_width
            self.camera.frame_height = config.frame_height
            self.camera.frame_center = content.get_center()[:2]

            self.wait(0.1)
            _save_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_t0_frame.png")
            self.wait(2.0)

            anim_duration = 2.5
            SignalFlow(
                clock,
                layout=layout,
                graph=graph,
                duration=anim_duration,
            ).play(self)
            WaveformSync(
                bundle,
                (clock, data),
                panel_spec=panel_spec,
                duration=anim_duration,
            ).play(self)
            self.wait(5.0)
            _save_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_last_frame.png")

except ImportError:
    pass
