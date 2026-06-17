"""Default beat plan factory and timing_mode dispatch."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.animation.base import AnimationPlan
from manim_engineering.animation.beat_factory import build_beat_plans
from manim_engineering.animation.style import TeachingStyle
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import derive_bundle_from_signals
from manim_engineering.waveform.rc import RCStepParams, derive_rc_waveform_bundle


def _clock_data_fixture():
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    drv.attach_to(graph)
    rcv.attach_to(graph)
    graph.connect(drv.get_pin("b"), rcv.get_pin("a"))
    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().layout(graph, elements)
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.get_pin("b"), rcv.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((clock,))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return graph, layout, clock, bundle, panel_spec


def _rc_fixture():
    graph, layout, vin, _bundle, _panel_spec = _clock_data_fixture()
    vc = Signal(name="vc", signal_type=SignalType.ANALOG, value=LogicState(level=LogicLevel.LOW))
    bundle = derive_rc_waveform_bundle(vin, vc, RCStepParams(t_end=2.0, sample_count=8))
    panel_spec = WaveformPanelRenderer().panel_spec_for_layout(layout, bundle)
    return graph, layout, vin, vc, bundle, panel_spec


def test_build_beat_plans_default_includes_flow_and_sync() -> None:
    graph, layout, clock, bundle, panel_spec = _clock_data_fixture()
    style = TeachingStyle()
    flow, sync, ramp, purpose = build_beat_plans(
        clock,
        layout=layout,
        graph=graph,
        record=clock.propagation_history[0],
        style=style,
        beat_duration=style.beat_duration,
        bundle=bundle,
        signals=(clock,),
        panel_spec=panel_spec,
        beat=0,
        reveal_tracker=None,
        reveal_time=None,
        wire_pulse=True,
        timing_mode="auto",
    )
    assert isinstance(flow, AnimationPlan)
    assert sync is not None
    assert ramp is None
    assert purpose == "timing"
    assert flow.animations


def test_build_beat_plans_timing_mode_sync_forces_waveform_sync() -> None:
    graph, layout, clock, bundle, panel_spec = _clock_data_fixture()
    style = TeachingStyle()
    _, sync, ramp, purpose = build_beat_plans(
        clock,
        layout=layout,
        graph=graph,
        record=clock.propagation_history[0],
        style=style,
        beat_duration=style.beat_duration,
        bundle=bundle,
        signals=(clock,),
        panel_spec=panel_spec,
        beat=0,
        reveal_tracker=None,
        reveal_time=None,
        wire_pulse=True,
        timing_mode="sync",
    )
    assert sync is not None
    assert ramp is None
    assert purpose == "timing"


def test_build_beat_plans_timing_mode_auto_uses_ramp_for_analog_reveal() -> None:
    graph, layout, _vin, vc, bundle, panel_spec = _rc_fixture()
    style = TeachingStyle()
    _, sync, ramp, purpose = build_beat_plans(
        vc,
        layout=layout,
        graph=graph,
        record=None,
        style=style,
        beat_duration=style.beat_duration,
        bundle=bundle,
        signals=(vc,),
        panel_spec=panel_spec,
        beat=0,
        reveal_tracker=None,
        reveal_time=1.0,
        wire_pulse=False,
        timing_mode="auto",
    )
    assert sync is None
    assert ramp is not None
    assert ramp.animations
    assert purpose == "timing"


def test_build_beat_plans_timing_mode_ramp_forces_analog_ramp() -> None:
    graph, layout, _vin, vc, bundle, panel_spec = _rc_fixture()
    style = TeachingStyle()
    _, sync, ramp, purpose = build_beat_plans(
        vc,
        layout=layout,
        graph=graph,
        record=None,
        style=style,
        beat_duration=style.beat_duration,
        bundle=bundle,
        signals=(vc,),
        panel_spec=panel_spec,
        beat=0,
        reveal_tracker=None,
        reveal_time=1.0,
        wire_pulse=False,
        timing_mode="ramp",
    )
    assert sync is None
    assert ramp is not None
    assert ramp.animations
    assert purpose == "timing"


@pytest.mark.parametrize("reveal_time", [None, 1.0])
def test_build_beat_plans_timing_mode_ramp_rejects_non_analog_inputs(
    reveal_time: float | None,
) -> None:
    graph, layout, clock, bundle, panel_spec = _clock_data_fixture()
    style = TeachingStyle()
    with pytest.raises(ValueError, match="requires analog trace and reveal_time"):
        build_beat_plans(
            clock,
            layout=layout,
            graph=graph,
            record=clock.propagation_history[0],
            style=style,
            beat_duration=style.beat_duration,
            bundle=bundle,
            signals=(clock,),
            panel_spec=panel_spec,
            beat=0,
            reveal_tracker=None,
            reveal_time=reveal_time,
            wire_pulse=True,
            timing_mode="ramp",
        )


def test_build_beat_plans_timing_mode_ramp_requires_reveal_time() -> None:
    graph, layout, _vin, vc, bundle, panel_spec = _rc_fixture()
    style = TeachingStyle()
    with pytest.raises(ValueError, match="requires analog trace and reveal_time"):
        build_beat_plans(
            vc,
            layout=layout,
            graph=graph,
            record=None,
            style=style,
            beat_duration=style.beat_duration,
            bundle=bundle,
            signals=(vc,),
            panel_spec=panel_spec,
            beat=0,
            reveal_tracker=None,
            reveal_time=None,
            wire_pulse=False,
            timing_mode="ramp",
        )


def test_build_beat_plans_timing_mode_none_skips_waveform() -> None:
    graph, layout, clock, bundle, panel_spec = _clock_data_fixture()
    style = TeachingStyle()
    flow, sync, ramp, purpose = build_beat_plans(
        clock,
        layout=layout,
        graph=graph,
        record=clock.propagation_history[0],
        style=style,
        beat_duration=style.beat_duration,
        bundle=bundle,
        signals=(clock,),
        panel_spec=panel_spec,
        beat=0,
        reveal_tracker=None,
        reveal_time=None,
        wire_pulse=True,
        timing_mode="none",
    )
    assert flow.animations
    assert sync is None
    assert ramp is None
    assert purpose is None
