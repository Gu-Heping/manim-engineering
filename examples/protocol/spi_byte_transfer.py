"""
SPI mode-0 byte transfer: layout, wires, clk/mosi/miso/cs waveforms, teaching beats.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim --disable_caching -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo``
Acceptance render: ``manim -qm examples/protocol/spi_byte_transfer.py SPIByteTransferDemo``
"""

from __future__ import annotations

from manim_engineering.animation import BeatSpec
from manim_engineering.components import SPIMaster, SPISlave
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutConfig, LayoutEngine
from manim_engineering.protocol.spi import SPIBusBinding, SPIController
from manim_engineering.waveform import derive_spi_waveform_bundle

TX_BYTE = 0xA5
RX_BYTE = 0x3C

# Static intro then motion-heavy beats. Per-beat duration is BEAT_DURATION,
# pacing comes from the shared pacing module. The subtitle band reserves
# vertical space for two HUD rows (title at row 0, caption/intro at row 1)
# above the topology; sized to clear the title + caption heights at the
# 3B1B font sizes (36 / 26) plus row_gap and a small breathing margin.
SPI_SUBTITLE_BAND = 1.25


def build_spi_fixture():
    """Return graph, elements, layout, SPI binding, transfer result, and waveform bundle."""
    graph = CircuitGraph()
    master = SPIMaster("master", label="MCU")
    slave = SPISlave("slave", label="SLV")
    master.attach_to(graph)
    slave.attach_to(graph)
    binding = SPIBusBinding.from_graph_nodes(graph, master_id="master", slave_id="slave")
    result = SPIController(binding).transfer_byte(TX_BYTE, rx_byte=RX_BYTE)

    elements = {"master": master, "slave": slave}
    layout = LayoutEngine(LayoutConfig(cell_gap=0.85)).layout(graph, elements)
    bundle = derive_spi_waveform_bundle(binding, result)
    return graph, elements, layout, binding, result, bundle


# Bit position MSB-first → SPIController iteration index. The controller
# records 2 clk entries per bit (rising then falling), so the rising edge for
# bit `b` (0 = MSB iteration, 7 = LSB iteration) is `history[2*b]`.
_BIT_LABELS = (
    ("位 7 (MSB)", 0),
    ("位 6", 1),
    ("位 5", 2),
    ("位 4", 3),
    ("位 3", 4),
    ("位 2", 5),
    ("位 1", 6),
    ("位 0 (LSB)", 7),
)

_CIRCLED = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")


def _teaching_beats(binding) -> tuple[BeatSpec, ...]:
    """One CS beat followed by every rising clk edge (nine beats total).

    Each beat has the correct caption / history-index pairing per
    ``SPIController._transfer_bit``. Earlier hand-written beat lists had
    mis-numbered labels because they treated each clk history entry as a
    full bit period rather than a half-period.
    """
    clk = binding.clk
    history = clk.propagation_history
    beats: list[BeatSpec] = [
        BeatSpec(
            signal=binding.cs,
            record=binding.cs.propagation_history[0],
            wave_beat=0,
            caption="① CS↓ 片选有效",
            reveal_time=0.0,
        ),
    ]
    for circle, (label, iter_index) in enumerate(_BIT_LABELS, start=2):
        wave_beat = 2 * iter_index
        beats.append(
            BeatSpec(
                signal=clk,
                record=history[wave_beat],
                wave_beat=wave_beat,
                caption=f"{_CIRCLED[circle - 1]} CLK↑ {label}",
                reveal_time=float(2 * iter_index),
            )
        )
    return tuple(beats)


def main() -> None:
    graph, elements, layout, binding, result, bundle = build_spi_fixture()
    print(f"SPI steps: {len(result.steps)}, timing events: {len(result.timing_events)}")
    print(f"tx=0x{result.tx_byte:02X} rx=0x{result.rx_byte:02X} fsm={result.final_fsm_state.value}")
    print(f"clk history: {len(binding.clk.propagation_history)} records")
    print(f"traces: {[t.signal_name for t in bundle.traces]}")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import WaveformDemoScene, WaveformFixture

    class SPIByteTransferDemo(WaveformDemoScene):
        """SPI bus: static intro then teaching beats (CS↓ + 8 CLK↑) with HUD captions.

        Follows 3B1B authoring conventions:
        - Background ``#1e1e2e`` applied via ``configure_waveform_scene_camera``.
        - Topology and waveform panel fade in (no bare ``add()``).
        - Each beat fades out the previous caption and fades in the next,
          then waits ``BEAT_CAPTION_HOLD`` so the eye reads before the pulse.
        - ``dim_inactive=True`` drops topology opacity between beats to keep
          the viewer's focus on the current bit.
        - Scene closes with ``FadeOut(*mobjects)`` instead of a hard cut.
        """

        subtitle_band = SPI_SUBTITLE_BAND
        dim_inactive = True
        intro_components_run_time = 0.7
        intro_pause_offset = 0.6

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, binding, result, bundle = build_spi_fixture()
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
                f"SPI Mode 0 · TX 0x{self._result.tx_byte:02X}  RX 0x{self._result.rx_byte:02X}",
                "静态介绍：MCU↔SLV 四线 clk/mosi/miso/cs + 波形",
            )

        def teaching_beats(self, _fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            return _teaching_beats(self._binding)

except ImportError:
    pass
