"""
Digital clock + data: layout, circuit render, waveform panel, SignalFlow + WaveformSync.

Two independent nets between DRV and RCV (clk on b→a, data on a→b).
Four teaching beats: clk↑, data↑, clk↓, data↓ with progressive waveform reveal.

Requires manim: ``pip install -e ".[manim]"``

Preview: ``manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo``
Acceptance render: ``manim -qm examples/basics/clock_data_waveform.py ClockDataWaveformDemo``
"""

from __future__ import annotations

from manim_engineering.animation import BEAT_DURATION, BeatSpec
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_falling_edge, record_rising_edge
from manim_engineering.waveform import derive_bundle_from_signals


def build_clock_data_fixture():
    """Return graph, elements, layout, clock/data signals, and derived waveform bundle."""
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    graph.add(drv)
    graph.add(rcv)
    clk_net = (drv.port_b, rcv.port_a)
    data_net = (drv.port_a, rcv.port_b)
    graph.connect(*clk_net)
    graph.connect(*data_net)

    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().solve(graph, elements)

    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))

    record_rising_edge(clock, *clk_net, graph=graph)
    record_rising_edge(data, *data_net, graph=graph)
    record_falling_edge(clock, *clk_net, graph=graph)
    record_falling_edge(data, *data_net, graph=graph)

    bundle = derive_bundle_from_signals((clock, data))
    return graph, elements, layout, clock, data, bundle


def main() -> None:
    graph, elements, layout, clock, data, bundle = build_clock_data_fixture()
    print(f"traces: {[t.signal_name for t in bundle.traces]}")
    print(f"connections: {len(graph.connections)}")
    print(f"clock transitions: {len(clock.propagation_history)}")
    print(f"beat_duration={BEAT_DURATION}s, traces={[t.signal_name for t in bundle.traces]}")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import (
        WaveformDemoScene,
        WaveformFixture,
        capture_camera_frame,
    )

    _ACCEPTANCE_MEDIA = Path("media/videos/clock_data_waveform")

    class ClockDataWaveformDemo(WaveformDemoScene):
        """DRV–RCV: separate clk/data nets, four beats, progressive waveforms."""

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, clock, data, bundle = build_clock_data_fixture()
            self._clock = clock
            self._data = data
            return WaveformFixture(
                graph=graph,
                elements=elements,
                layout=layout,
                bundle=bundle,
                signals=(clock, data),
            )

        def teaching_beats(self, _fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            ch = self._clock.propagation_history
            dh = self._data.propagation_history
            return (
                BeatSpec(signal=self._clock, record=ch[0], wave_beat=0),
                BeatSpec(signal=self._data, record=dh[0], wave_beat=0),
                BeatSpec(signal=self._clock, record=ch[1], wave_beat=1),
                BeatSpec(signal=self._data, record=dh[1], wave_beat=1),
            )

        def after_intro_hook(self, _fixture, _camera) -> None:
            capture_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_t0_frame.png")

        def after_beats_hook(self, _fixture, _camera) -> None:
            capture_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_last_frame.png")

except ImportError:
    pass
