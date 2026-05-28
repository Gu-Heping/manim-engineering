"""
RC充电演示：InputDriver → R1 → C1 → GND。

Preview: ``manim -pql examples/analog/01_rc_charge.py RCChargeScene``
"""

from __future__ import annotations

from manim_engineering.animation import BeatSpec
from manim_engineering.components import Capacitor, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal, record_analog_level_between_pins, record_rising_edge
from manim_engineering.waveform import RCStepParams, derive_rc_waveform_bundle, rc_charge_level_normalized

RC_SUBTITLE_BAND = 1.25
RC_PARAMS = RCStepParams(v_src=5.0, tau=1.0, t_step=0.0, t_end=5.0, sample_count=32)


def build_rc_charge_fixture():
    graph = CircuitGraph()
    drv = InputDriver("drv", label="IN", signal_type=SignalType.DIGITAL)
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    gnd = Ground("gnd", label="GND")
    for comp in (drv, r1, c1, gnd):
        comp.attach_to(graph)
    graph.connect(drv.get_pin("out"), r1.get_pin("a"))
    graph.connect(r1.get_pin("b"), c1.get_pin("a"))
    graph.connect(c1.get_pin("b"), gnd.get_pin("gnd"))
    elements = {"drv": drv, "r1": r1, "c1": c1, "gnd": gnd}
    layout = LayoutEngine().solve(graph, elements)
    return graph, elements, layout


def build_rc_teaching_fixture():
    graph, elements, layout = build_rc_charge_fixture()
    drv = elements["drv"]
    r1 = elements["r1"]
    c1 = elements["c1"]

    vin = Signal(
        name="vin",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    vc = Signal(name="vc", signal_type=SignalType.ANALOG, value=0.0)

    vin_record = record_rising_edge(vin, drv.get_pin("out"), r1.get_pin("a"), graph=graph)
    charge_2tau = rc_charge_level_normalized(2.0 * RC_PARAMS.tau, RC_PARAMS)
    vc_record = record_analog_level_between_pins(
        vc,
        r1.get_pin("b"),
        c1.get_pin("a"),
        charge_2tau,
        graph=graph,
    )

    bundle = derive_rc_waveform_bundle(vin, vc, RC_PARAMS)
    signals = (vin, vc)
    records = (vin_record, vc_record)
    return graph, elements, layout, signals, bundle, records


def _teaching_beats(signals, records) -> tuple[BeatSpec, ...]:
    vin, vc = signals
    vin_record, vc_record = records
    return (
        BeatSpec(
            signal=vin,
            record=vin_record,
            wave_beat=0,
            caption="① IN 阶跃 · 输入电压跳变",
            emphasis="context",
            wire_pulse=False,
        ),
        BeatSpec(
            signal=vc,
            record=vc_record,
            caption="② V_C 指数上升 · τ = R·C",
            emphasis="key",
            reveal_time=2.0 * RC_PARAMS.tau,
            reveal_scope="signal",
            wire_pulse=False,
        ),
    )


def main() -> None:
    graph, elements, layout, signals, bundle, records = build_rc_teaching_fixture()
    print(f"nodes={len(graph.nodes)} wires={len(layout.wires)} traces={[t.signal_name for t in bundle.traces]}")
    print(f"beats={len(_teaching_beats(signals, records))} vc@2τ={records[1].new_value:.3f}")


if __name__ == "__main__":
    main()


RCChargeScene = None

try:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from _shared import WaveformDemoScene, WaveformFixture

    class RCChargeScene(WaveformDemoScene):
        """RC充电回路：阶跃输入 + 电容电压指数曲线。"""

        subtitle_band = RC_SUBTITLE_BAND
        camera_target_fill = 0.85
        dim_inactive = False
        intro_components_run_time = 0.7
        intro_pause_offset = 0.6
        play_waveform_baseline = False
        extend_waveform_to_panel = False

        def build_fixture(self) -> WaveformFixture:
            graph, elements, layout, signals, bundle, records = build_rc_teaching_fixture()
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
                "RC充电回路 · IN→R1→C1→GND",
                "静态介绍：阶跃输入驱动 RC，观察 V_C(t) 指数上升",
            )

        def teaching_beats(self, fixture: WaveformFixture) -> tuple[BeatSpec, ...]:
            return _teaching_beats(fixture.signals, self._records)

except ImportError:
    RCChargeScene = None
