"""RC step-response waveform derivation."""

from __future__ import annotations

import pytest

from manim_engineering.core.enums import SignalType
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import (
    InvalidWaveformParamsError,
    RCStepParams,
    derive_rc_waveform_bundle,
    rc_charge_level_normalized,
    rc_charge_samples,
    rc_charge_voltage,
)


def test_rc_charge_voltage_is_zero_before_step() -> None:
    params = RCStepParams(v_src=5.0, tau=1.0, t_step=0.5)
    assert rc_charge_voltage(0.0, params) == 0.0
    assert rc_charge_voltage(0.49, params) == 0.0


def test_rc_charge_voltage_approaches_v_src() -> None:
    params = RCStepParams(v_src=5.0, tau=1.0, t_step=0.0, t_end=10.0)
    assert rc_charge_voltage(0.0, params) == 0.0
    assert rc_charge_level_normalized(0.0, params) == 0.0
    assert rc_charge_level_normalized(10.0, params) == pytest.approx(1.0, rel=1e-3)


def test_rc_charge_samples_are_monotonic_and_deterministic() -> None:
    params = RCStepParams(sample_count=16)
    first = rc_charge_samples(params)
    second = rc_charge_samples(params)
    assert first == second
    levels = [sample.level for sample in first if isinstance(sample.level, float)]
    assert levels == sorted(levels)
    assert first[0].time == 0.0
    assert first[0].level == 0.0


def test_derive_rc_waveform_bundle_trace_shapes() -> None:
    vin = Signal(name="vin", signal_type=SignalType.DIGITAL, value=LogicState(level=LogicLevel.LOW))
    vc = Signal(name="vc", signal_type=SignalType.ANALOG, value=0.0)
    params = RCStepParams(sample_count=8)
    bundle = derive_rc_waveform_bundle(vin, vc, params)

    vin_trace = bundle.trace_named("vin")
    vc_trace = bundle.trace_named("vc")
    assert vin_trace is not None and vin_trace.is_discrete
    assert vc_trace is not None and not vc_trace.is_discrete
    assert len(vin_trace.samples) == 2
    assert len(vc_trace.samples) == params.sample_count


def test_rc_charge_samples_rejects_non_positive_tau() -> None:
    with pytest.raises(InvalidWaveformParamsError, match="tau"):
        rc_charge_samples(RCStepParams(tau=0.0))


def test_rc_charge_samples_rejects_inverted_time_span() -> None:
    with pytest.raises(InvalidWaveformParamsError, match="t_end"):
        rc_charge_samples(RCStepParams(t_step=2.0, t_end=1.0))


def test_rc_charge_samples_rejects_low_sample_count() -> None:
    with pytest.raises(InvalidWaveformParamsError, match="sample_count"):
        rc_charge_samples(RCStepParams(sample_count=1))
