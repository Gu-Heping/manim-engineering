"""
UART 8N1 byte transmit: layout, TX line waveform, SignalFlow + WaveformSync.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/protocol/uart_byte_transfer.py UARTByteTransferDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, WaveformSync
from manim_engineering.components import UARTPort
from manim_engineering.layout import LayoutEngine
from manim_engineering.protocol.uart import UARTBinding, UARTController
from manim_engineering.renderers.minimal import MinimalRenderer, WaveformPanelRenderer
from manim_engineering.semantic import CircuitGraph
from manim_engineering.waveform import derive_bundle_from_signals

TX_BYTE = 0xA5


def build_fixture():
    """Return graph, elements, layout, UART binding, transfer result, and waveform bundle."""
    graph = CircuitGraph()
    transmitter = UARTPort("tx_dev", label="MCU TX")
    receiver = UARTPort("rx_dev", label="HOST RX")
    transmitter.attach_to(graph)
    receiver.attach_to(graph)
    binding = UARTBinding.from_graph_nodes(
        graph,
        transmitter_id="tx_dev",
        receiver_id="rx_dev",
    )
    result = UARTController(binding, baud_rate=115200).transmit_byte(TX_BYTE)

    elements = {"tx_dev": transmitter, "rx_dev": receiver}
    layout = LayoutEngine().layout(graph, elements)
    bundle = derive_bundle_from_signals(binding.signals())
    return graph, elements, layout, binding, result, bundle


def main() -> None:
    graph, elements, layout, binding, result, bundle = build_fixture()
    print(f"UART steps: {len(result.steps)}, timing events: {len(result.timing_events)}")
    print(
        f"tx=0x{result.tx_byte:02X} fsm={result.final_fsm_state.value} "
        f"bit_period={result.bit_period}"
    )
    print(f"traces: {[t.signal_name for t in bundle.traces]}")
    print(f"connections: {len(graph.connections)}")
    flow = SignalFlow(binding.tx, layout=layout, graph=graph)
    sync = WaveformSync(
        bundle,
        binding.signals(),
        panel_spec=WaveformPanelRenderer().panel_spec_for_layout(layout, bundle),
    )
    print(f"SignalFlow run_time={flow.build().run_time}s, sync beat={sync.resolved_beat()}")


if __name__ == "__main__":
    main()


try:
    from manim import Scene, VGroup

    class UARTByteTransferDemo(Scene):
        """UART TX line layout with waveform panel and propagation/timing sync."""

        def construct(self) -> None:
            graph, elements, layout, binding, _result, bundle = build_fixture()
            circuit = MinimalRenderer().render_layout(layout, graph, elements)
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            self.add(VGroup(circuit, waveform_panel))

            SignalFlow(binding.tx, layout=layout, graph=graph).play(self)
            WaveformSync(
                bundle,
                binding.signals(),
                panel_spec=panel_spec,
            ).play(self)

except ImportError:
    pass
