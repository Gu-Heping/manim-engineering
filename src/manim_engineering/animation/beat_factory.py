"""Default beat plan factory: SignalFlow + WaveformSync / AnalogRamp dispatch."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from manim_engineering.animation.analog_ramp import AnalogRamp
from manim_engineering.animation.base import AnimationPlan
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.signal_flow import SignalFlow
from manim_engineering.animation.style import TeachingStyle
from manim_engineering.animation.waveform_controller import WaveformSegmentController
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.animation.waveform_sync import WaveformSync
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle

TimingMode = Literal["auto", "sync", "ramp", "none"]


def build_beat_plans(
    signal: Signal,
    *,
    layout: LayoutResult,
    graph: CircuitGraph | None,
    record: PropagationRecord | None,
    style: TeachingStyle,
    beat_duration: float,
    bundle: WaveformBundle | None,
    signals: Sequence[Signal],
    panel_spec: WaveformPanelSpec | None,
    beat: int | None,
    waveform_controller: WaveformSegmentController | None = None,
    reveal_tracker: WaveformRevealTracker | None = None,
    reveal_time: float | None = None,
    wire_pulse: bool = True,
    timing_mode: TimingMode = "auto",
) -> tuple[AnimationPlan, AnimationPlan | None, AnimationPlan | None, str | None]:
    """Return ``(flow_plan, sync_plan, ramp_plan, timing_purpose)`` for one beat."""

    if wire_pulse:
        flow = SignalFlow(
            signal,
            record=record,
            layout=layout,
            graph=graph,
            duration=beat_duration,
            flash_time_width=style.pulse_flash_width,
            wire_flash_time_width=style.wire_flash_width,
        )
        flow_plan = flow.build()
    else:
        flow_plan = AnimationPlan(
            overlays=(),
            propagation_overlays=(),
            animations=(),
            run_time=beat_duration,
        )

    sync_plan = None
    ramp_plan = None
    timing_purpose: str | None = None
    ramp_t_start = 0.0
    if waveform_controller is None and reveal_tracker is not None:
        waveform_controller = WaveformSegmentController(reveal_tracker)
    if waveform_controller is not None:
        ramp_t_start = waveform_controller.revealed_time_for(signal.name)

    if bundle is not None and panel_spec is not None and signals and timing_mode != "none":
        trace_match = bundle.trace_named(signal.name)
        use_ramp = timing_mode == "ramp"
        if timing_mode == "auto":
            use_ramp = (
                reveal_time is not None
                and trace_match is not None
                and not trace_match.is_discrete
            )
        elif timing_mode == "sync":
            use_ramp = False

        if use_ramp:
            if trace_match is None or reveal_time is None or trace_match.is_discrete:
                msg = "timing_mode='ramp' requires analog trace and reveal_time"
                raise ValueError(msg)
            trace_index = next(
                index
                for index, trace in enumerate(bundle.traces)
                if trace.signal_name == signal.name
            )
            ramp = AnalogRamp(
                trace_match,
                panel_spec=panel_spec,
                trace_index=trace_index,
                t_start=ramp_t_start,
                t_end=reveal_time,
                duration=beat_duration,
            )
            ramp_plan = ramp.build()
            timing_purpose = AnimationPurpose.TIMING.value
        elif timing_mode in ("auto", "sync"):
            sync = WaveformSync(
                bundle,
                signals,
                panel_spec=panel_spec,
                beat=beat,
                duration=beat_duration,
                active_signal=signal,
                flash_time_width=style.waveform_flash_width,
            )
            sync_plan = sync.build()
            timing_purpose = AnimationPurpose.TIMING.value

    return flow_plan, sync_plan, ramp_plan, timing_purpose
