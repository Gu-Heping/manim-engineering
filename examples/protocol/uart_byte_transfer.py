"""
UART 8N1 byte transmit: layout, TX line waveform, parallel propagation beat.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/protocol/uart_byte_transfer.py UARTByteTransferDemo``
"""

from __future__ import annotations

from manim_engineering.animation import BeatSpec
from manim_engineering.components import UARTPort
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import Point2D
from manim_engineering.protocol.uart import UARTBinding, UARTController
from manim_engineering.waveform import derive_bundle_from_signals

TX_BYTE = 0xA5
# Reserves vertical space for two HUD rows (title row 0, caption row 1) above
# the topology. See spi_byte_transfer for sizing rationale.
UART_SUBTITLE_BAND = 1.25

# MCU TX on the left, HOST RX on the right — horizontal cross-link.
UART_OVERRIDES: dict[str, Point2D] = {
    "tx_dev": Point2D(-2.2, 0.0),
    "rx_dev": Point2D(2.2, 0.0),
}


def build_uart_fixture():
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
    layout = LayoutEngine().layout(graph, elements, placement_overrides=UART_OVERRIDES)
    bundle = derive_bundle_from_signals(binding.signals())
    return graph, elements, layout, binding, result, bundle


_BIT_CIRCLED = ("②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨")


def _teaching_beats(binding, tx_byte: int) -> tuple[BeatSpec, ...]:
    """Start, 8 LSB-first data bits, stop — every UART propagation event.

    The transmitter records exactly ``1 + 8 + 1`` ``PropagationRecord``s, so
    ``binding.tx.propagation_history`` indexes line up 1:1 with the trace's
    edge list (``wave_beat = history index``).
    """
    history = binding.tx.propagation_history
    beats: list[BeatSpec] = [
        BeatSpec(
            signal=binding.tx,
            record=history[0],
            wave_beat=0,
            caption="① Start ↓ (LOW)",
        ),
    ]
    for bit_index in range(8):
        level = "HIGH" if (tx_byte >> bit_index) & 1 else "LOW"
        beats.append(
            BeatSpec(
                signal=binding.tx,
                record=history[1 + bit_index],
                wave_beat=1 + bit_index,
                caption=f"{_BIT_CIRCLED[bit_index]} 位 {bit_index} = {level}",
            )
        )
    beats.append(
        BeatSpec(
            signal=binding.tx,
            record=history[9],
            wave_beat=9,
            caption="⑩ Stop ↑ (HIGH)",
        )
    )
    return tuple(beats)


def main() -> None:
    graph, elements, layout, binding, result, bundle = build_uart_fixture()
    print(f"UART steps: {len(result.steps)}, timing events: {len(result.timing_events)}")
    print(
        f"tx=0x{result.tx_byte:02X} fsm={result.final_fsm_state.value} "
        f"bit_period={result.bit_period}"
    )
    print(f"traces: {[t.signal_name for t in bundle.traces]}")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import WaveformDemoScene, WaveformFixture

    class UARTByteTransferDemo(WaveformDemoScene):
        """UART 8N1 byte: 10 teaching beats (start + 8 data + stop) with HUD captions.

        Same 3B1B authoring conventions as ``SPIByteTransferDemo``:
        intro fades in piece by piece, caption→caption crossfades, viewer gets
        ``BEAT_CAPTION_HOLD`` to read before each pulse, scene closes with a
        full FadeOut.
        """

        subtitle_band = UART_SUBTITLE_BAND
        dim_inactive = True
        intro_components_run_time = 0.7
        intro_total_run_time = 1.4
        intro_pause_offset = 0.6

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, binding, result, bundle = build_uart_fixture()
            self._binding = binding
            self._result = result
            return WaveformFixture(
                graph=graph,
                elements=elements,
                layout=layout,
                bundle=bundle,
                signals=tuple(binding.signals()),
            )

        def hud_texts(self, _fixture: WaveformFixture) -> tuple[str, str]:
            return (
                f"UART 8N1 · TX 0x{self._result.tx_byte:02X} (LSB first)",
                "静态介绍：MCU→HOST tx 线，idle HIGH，下降沿 Start",
            )

        def teaching_beats(self, _fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            return _teaching_beats(self._binding, self._result.tx_byte)

except ImportError:
    pass
