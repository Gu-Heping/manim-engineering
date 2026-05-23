"""
Three-resistor signal chain: clk and data on separate net segments.

Demonstrates **digital edge propagation along passive net segments**
(R1–R2 and R2–R3). Trace labels ``net12`` / ``net23`` name the link under
test — not a clock/data bus or power-rail demo.

Preview: ``manim -pql examples/basics/signal_chain_demo.py SignalChainDemo``
"""

from __future__ import annotations

from manim_engineering.animation import BEAT_DURATION, BeatSpec
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_falling_edge, record_rising_edge
from manim_engineering.waveform import derive_bundle_from_signals


def build_signal_chain_fixture():
    """Three-resistor chain. Clock and data each propagate along their own link."""
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

    clk_net = (r1.get_pin("b"), r2.get_pin("a"))
    data_net = (r2.get_pin("b"), r3.get_pin("a"))

    net12 = Signal(
        name="net12",
        signal_type=SignalType.SIGNAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    net23 = Signal(
        name="net23",
        signal_type=SignalType.SIGNAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    record_rising_edge(net12, *clk_net, graph=graph)
    record_rising_edge(net23, *data_net, graph=graph)
    record_falling_edge(net12, *clk_net, graph=graph)
    record_falling_edge(net23, *data_net, graph=graph)

    bundle = derive_bundle_from_signals((net12, net23))
    return graph, elements, layout, net12, net23, bundle


def main() -> None:
    graph, elements, layout, net12, net23, bundle = build_signal_chain_fixture()
    print(f"components: {list(elements.keys())}")
    print(f"connections: {len(graph.connections)}")
    print(f"traces: {['net12', 'net23']}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(f"beat_duration={BEAT_DURATION}s")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import WaveformDemoScene, WaveformFixture

    class SignalChainDemo(WaveformDemoScene):
        """Three-resistor chain: net12 on R1–R2, net23 on R2–R3, four beats."""

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, net12, net23, bundle = build_signal_chain_fixture()
            self._net12 = net12
            self._net23 = net23
            return WaveformFixture(
                graph=graph,
                elements=elements,
                layout=layout,
                bundle=bundle,
                signals=(net12, net23),
            )

        def teaching_beats(self, _fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            h12 = self._net12.propagation_history
            h23 = self._net23.propagation_history
            return (
                BeatSpec(signal=self._net12, record=h12[0], wave_beat=0),
                BeatSpec(signal=self._net23, record=h23[0], wave_beat=0),
                BeatSpec(signal=self._net12, record=h12[1], wave_beat=1),
                BeatSpec(signal=self._net23, record=h23[1], wave_beat=1),
            )

except ImportError:
    pass
