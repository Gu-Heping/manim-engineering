"""
CMOS反相器演示：VCC → PMOS → OUT → NMOS → GND, IN驱动两管栅极。

Preview: ``manim -pql examples/analog/03_cmos_inverter.py CMOSInverterScene``
"""

from __future__ import annotations

from collections.abc import Mapping

from manim_engineering.animation import BeatSpec, TeachingStyle
from manim_engineering.components import (
    NMOS,
    PMOS,
    VCC,
    CircuitElement,
    Ground,
    InputDriver,
)
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import layout_from_preset
from manim_engineering.layout.presets.cmos_inverter import cmos_inverter_preset
from manim_engineering.layout.types import LayoutResult
from manim_engineering.semantic import (
    LogicLevel,
    LogicState,
    Signal,
    record_falling_edge,
    record_rising_edge,
)
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.waveform import derive_bundle_from_signals
from manim_engineering.waveform.trace import WaveformBundle

CMOS_SUBTITLE_BAND = 1.2


def build_inverter_fixture():
    graph = CircuitGraph()
    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    pmos = PMOS("pm1", label="P1")
    nmos = NMOS("nm1", label="N1")
    in_drv = InputDriver("in_drv", label="IN", signal_type=SignalType.DIGITAL)
    for comp in (vcc, gnd, pmos, nmos, in_drv):
        comp.attach_to(graph)
    graph.connect(vcc.get_pin("vcc"), pmos.get_pin("source"))
    graph.connect(pmos.get_pin("drain"), nmos.get_pin("drain"))
    graph.connect(pmos.get_pin("bulk"), pmos.get_pin("source"))
    graph.connect(nmos.get_pin("source"), gnd.get_pin("gnd"))
    graph.connect(nmos.get_pin("bulk"), nmos.get_pin("source"))
    graph.connect(in_drv.get_pin("out"), pmos.get_pin("gate"))
    graph.connect(in_drv.get_pin("out"), nmos.get_pin("gate"))
    elements = {"vcc1": vcc, "gnd1": gnd, "pm1": pmos, "nm1": nmos, "in_drv": in_drv}
    preset = cmos_inverter_preset(vcc, gnd, pmos, nmos, in_drv)
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    return graph, elements, layout


def build_cmos_teaching_fixture() -> tuple[
    CircuitGraph,
    Mapping[str, CircuitElement],
    LayoutResult,
    tuple[Signal, Signal],
    WaveformBundle,
    tuple[PropagationRecord, PropagationRecord],
]:
    graph, elements, layout = build_inverter_fixture()
    in_drv = elements["in_drv"]
    pmos = elements["pm1"]
    nmos = elements["nm1"]

    vin = Signal(
        name="vin",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    vout = Signal(
        name="vout",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.HIGH),
    )

    vin_record = record_rising_edge(
        vin,
        in_drv.get_pin("out"),
        pmos.get_pin("gate"),
        graph=graph,
    )
    vout_record = record_falling_edge(
        vout,
        pmos.get_pin("drain"),
        nmos.get_pin("drain"),
        graph=graph,
    )

    bundle = derive_bundle_from_signals((vin, vout), time_step=1.0)
    signals = (vin, vout)
    records = (vin_record, vout_record)
    return graph, elements, layout, signals, bundle, records


def _teaching_beats(signals, records) -> tuple[BeatSpec, ...]:
    vin, vout = signals
    vin_record, vout_record = records
    return (
        BeatSpec(
            signal=vin,
            record=vin_record,
            wave_beat=0,
            caption="① IN↑ · 栅极被拉高",
            transition_profile="setup",
            emphasis="context",
            wire_pulse=False,
        ),
        BeatSpec(
            signal=vout,
            record=vout_record,
            wave_beat=0,
            caption="② OUT↓ · 反相器输出翻转",
            transition_profile="conclusion",
            emphasis="key",
            wire_pulse=False,
        ),
    )


def main() -> None:
    graph, elements, layout, signals, bundle, records = build_cmos_teaching_fixture()
    print(
        f"nodes={len(graph.nodes)} wires={len(layout.wires)} "
        f"traces={[t.signal_name for t in bundle.traces]}"
    )
    print(f"beats={len(_teaching_beats(signals, records))}")


if __name__ == "__main__":
    main()


CMOSInverterScene = None

try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import WaveformDemoScene, WaveformFixture

    class CMOSInverterScene(WaveformDemoScene):
        """CMOS反相器：IN↑ 后 OUT 反相下降。"""

        subtitle_band = CMOS_SUBTITLE_BAND
        camera_target_fill = 0.75
        dim_inactive = False
        intro_pause_offset = 0.6
        style = TeachingStyle(
            setup_caption_hold_scale=1.2,
            setup_post_hold=0.16,
            conclusion_caption_hold_scale=1.45,
            conclusion_post_hold=0.36,
        )

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, signals, bundle, records = build_cmos_teaching_fixture()
            self._records = records
            return WaveformFixture(
                graph=graph,
                elements=elements,
                layout=layout,
                bundle=bundle,
                signals=signals,
            )

        def hud_texts(self, _fixture: WaveformFixture) -> tuple[str, str]:
            return (
                "CMOS Inverter · VCC→P1→OUT→N1→GND",
                "互补 MOS 对：IN 驱动 P/N 栅极，OUT 与 IN 反相",
            )

        def hud_intro_texts(self, _fixture: WaveformFixture) -> tuple[str, str]:
            return (
                "CMOS Inverter",
                "互补 MOS 对：IN 驱动双管栅极，观察反相过程",
            )

        def teaching_beats(self, fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            return _teaching_beats(fixture.signals, self._records)

except ImportError:
    CMOSInverterScene = None
