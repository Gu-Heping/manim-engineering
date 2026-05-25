"""RC step-response waveform bundle (teaching-first, no SPICE)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from manim_engineering.core.enums import SignalType
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.derive import _resolve_pin_id
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace


@dataclass(frozen=True)
class RCStepParams:
    """Teaching parameters for a single RC charge curve."""

    v_src: float = 5.0
    tau: float = 1.0
    t_step: float = 0.0
    t_end: float = 5.0
    sample_count: int = 32


def rc_charge_voltage(t: float, params: RCStepParams) -> float:
    """Physical voltage at semantic time ``t`` (volts, not normalized)."""
    if t < params.t_step:
        return 0.0
    return params.v_src * (1.0 - math.exp(-(t - params.t_step) / params.tau))


def rc_charge_level_normalized(t: float, params: RCStepParams) -> float:
    """Normalized capacitor voltage in ``[0, 1]`` for waveform Y mapping."""
    if params.v_src <= 0.0:
        return 0.0
    return rc_charge_voltage(t, params) / params.v_src


def rc_charge_samples(params: RCStepParams) -> tuple[WaveformSample, ...]:
    """Dense analog samples for ``V_C(t)`` on the shared semantic time axis."""
    if params.sample_count < 2:
        msg = "sample_count must be >= 2"
        raise ValueError(msg)
    samples: list[WaveformSample] = []
    samples.append(WaveformSample(time=0.0, level=0.0))
    span = params.t_end - params.t_step
    for index in range(1, params.sample_count):
        t = params.t_step + span * index / (params.sample_count - 1)
        samples.append(WaveformSample(time=t, level=rc_charge_level_normalized(t, params)))
    return tuple(samples)


def derive_rc_waveform_bundle(
    vin: Signal,
    vc: Signal,
    params: RCStepParams,
) -> WaveformBundle:
    """Build ``vin`` (digital step) + ``vc`` (smooth analog) traces for RC teaching."""
    vin_trace = WaveformTrace(
        signal_name=vin.name,
        signal_type=vin.signal_type,
        pin_id=_resolve_pin_id(vin, None),
        samples=(
            WaveformSample(time=0.0, level=LogicLevel.LOW),
            WaveformSample(time=params.t_step, level=LogicLevel.HIGH),
        ),
        is_discrete=True,
    )
    vc_trace = WaveformTrace(
        signal_name=vc.name,
        signal_type=SignalType.ANALOG,
        pin_id=_resolve_pin_id(vc, None),
        samples=rc_charge_samples(params),
        is_discrete=False,
    )
    return WaveformBundle(traces=(vin_trace, vc_trace))
