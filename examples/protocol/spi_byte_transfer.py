"""
SPI mode-0 byte transfer: layout, wires, clk/mosi/miso/cs waveforms, SignalFlow + WaveformSync.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo``
"""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, WaveformSync
from manim_engineering.components import SPIMaster, SPISlave
from manim_engineering.layout import LayoutEngine
from manim_engineering.protocol.spi import SPIBusBinding, SPIController
from manim_engineering.renderers.minimal import MinimalRenderer, WaveformPanelRenderer
from manim_engineering.semantic import CircuitGraph
from manim_engineering.waveform import derive_bundle_from_signals

TX_BYTE = 0xA5
RX_BYTE = 0x3C


def build_fixture():
    """Return graph, elements, layout, SPI binding, transfer result, and waveform bundle."""
    graph = CircuitGraph()
    master = SPIMaster("master", label="MCU")
    slave = SPISlave("slave", label="SLV")
    master.attach_to(graph)
    slave.attach_to(graph)
    binding = SPIBusBinding.from_graph_nodes(graph, master_id="master", slave_id="slave")
    result = SPIController(binding).transfer_byte(TX_BYTE, rx_byte=RX_BYTE)

    elements = {"master": master, "slave": slave}
    layout = LayoutEngine().layout(graph, elements)
    bundle = derive_bundle_from_signals(binding.signals())
    return graph, elements, layout, binding, result, bundle


def main() -> None:
    graph, elements, layout, binding, result, bundle = build_fixture()
    print(f"SPI steps: {len(result.steps)}, timing events: {len(result.timing_events)}")
    print(f"tx=0x{result.tx_byte:02X} rx=0x{result.rx_byte:02X} fsm={result.final_fsm_state.value}")
    print(f"traces: {[t.signal_name for t in bundle.traces]}")
    print(f"connections: {len(graph.connections)}")
    flow = SignalFlow(binding.clk, layout=layout, graph=graph)
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

    class SPIByteTransferDemo(Scene):
        """SPI bus layout with waveform panel and propagation/timing sync."""

        def construct(self) -> None:
            graph, elements, layout, binding, _result, bundle = build_fixture()
            circuit = MinimalRenderer().render_layout(layout, graph, elements)
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(bundle, layout)
            self.add(VGroup(circuit, waveform_panel))

            SignalFlow(binding.clk, layout=layout, graph=graph).play(self)
            WaveformSync(
                bundle,
                binding.signals(),
                panel_spec=panel_spec,
            ).play(self)

except ImportError:
    pass
