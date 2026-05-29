"""Multi-beat propagation: successive SignalFlow + optional WaveformSync.

Supports two modes:

1. **Single-signal**: replays one signal's propagation history (``records``).
2. **Heterogeneous beats**: explicit per-beat ``BeatSpec`` so SPI/UART/etc.
   can advance different signals (CS↓ then CLK↑ … CLK↑) within one sequence
   while still sharing pacing, dimming, and caption callbacks.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from manim import AnimationGroup, LaggedStart, ShowPassingFlash

from manim_engineering.animation.beat import play_propagation_beat
from manim_engineering.animation.beat_factory import TimingMode
from manim_engineering.animation.errors import BeatAnimationError
from manim_engineering.animation.focus import dim_topology, restore_topology
from manim_engineering.animation.label_phase import (
    LabelPhasePolicy,
    label_allowed_in_phase,
    phase_for_transition_profile,
)
from manim_engineering.animation.pacing import BEAT_CAPTION_HOLD, BEAT_DURATION, BEAT_GAP
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.stage_record import record_signal_stage, wait_signal_stage
from manim_engineering.animation.style import EmphasisLevel, TeachingStyle, style_for_emphasis
from manim_engineering.animation.trace import maybe_snapshot_stage, record_stage
from manim_engineering.animation.waveform_controller import WaveformSegmentController
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.animation.wires import (
    connection_id_for_pins,
    oriented_wire_points,
    path_mobject_from_points,
    wire_path_for_connection,
)
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.renderers.minimal import theme as renderer_theme
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    iter_label_roots,
    label_target_opacity,
    label_visible,
    refresh_label_strokes,
    set_label_visible,
)
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle

TransitionProfile = Literal["default", "setup", "conclusion"]


@dataclass(frozen=True)
class BeatSpec:
    """One beat in a heterogeneous propagation sequence.

    Attributes:
        signal: The semantic signal whose pulse travels this beat.
        record: Propagation record describing the wire segment.
        wave_beat: Index into the trace edge history for ``WaveformSync``;
            ``None`` for "use the latest" semantics.
        caption: Optional teaching string surfaced via ``caption_callback``.
        reveal_targets: Optional ``(signal, max_beat)`` pairs for progressive
            waveform panel reveal. When omitted, defaults to
            ``(signal, wave_beat or beat_index)``.
        reveal_time: When set, the panel advances to this semantic time
            (requires ``reveal_tracker`` on the sequence). Scope is controlled
            by ``reveal_scope``.
        reveal_scope: ``"all"`` advances every trace (SPI shared axis);
            ``"signal"`` advances only ``signal.name``.
        wire_pulse: When ``False``, skip :class:`SignalFlow` and keep waveform
            timing/reveal only (analog teaching beats).
        duration: Per-beat run_time override; ``None`` defers to the
            sequence-level ``beat_duration``. Use for emphasis (slower) or
            quick setup transitions (faster).
        transition_profile: Optional beat-level motion profile
            (``default`` | ``setup`` | ``conclusion``). This is the preferred
            authoring entry for phased teaching motion.
        emphasis: Optional beat-level emphasis preset (``context`` |
            ``normal`` | ``key``) retained as a compatibility alias for
            transition-profile defaults.
        style: Optional beat-level :class:`TeachingStyle` override.
        timing_mode: Override waveform timing dispatch (``auto`` | ``sync`` |
            ``ramp`` | ``none``).
    """

    signal: Signal
    record: PropagationRecord
    wave_beat: int | None = None
    caption: str | None = None
    reveal_targets: tuple[tuple[Signal, int], ...] | None = None
    reveal_time: float | None = None
    reveal_scope: Literal["all", "signal"] = "all"
    wire_pulse: bool = True
    duration: float | None = None
    transition_profile: TransitionProfile | None = None
    emphasis: EmphasisLevel | None = None
    style: TeachingStyle | None = None
    timing_mode: TimingMode = "auto"


@dataclass(frozen=True)
class _BeatContext:
    index: int
    spec: BeatSpec
    style: TeachingStyle
    transition_profile: TransitionProfile
    reveal_time: float | None
    reveal_targets: tuple[tuple[Signal, int], ...] | None

    @property
    def signal(self) -> Signal:
        return self.spec.signal

    @property
    def beat(self) -> int:
        return self.spec.wave_beat if self.spec.wave_beat is not None else self.index


@dataclass(frozen=True)
class _TopologyFocusPlan:
    run_time: float
    endpoint_emphasis: bool
    animations: tuple[object, ...]


@dataclass(frozen=True)
class _LabelFocusPlan:
    run_time: float
    label_phase: str
    labels: tuple[object, ...]


@dataclass(frozen=True)
class _WaitStagePlan:
    stage: str
    run_time: float
    detail: dict[str, object]
    purpose: str | None = None


@dataclass(frozen=True)
class _PreludePlan:
    topology_focus_enabled: bool
    topology_focus_settle: _WaitStagePlan | None
    caption_settle: _WaitStagePlan | None
    label_focus_settle: _WaitStagePlan | None


@dataclass(frozen=True)
class _PostludePlan:
    post_hold: _WaitStagePlan | None


class PropagationSequence:
    """Play multiple propagation beats in order with comprehension gaps.

    Does not call :meth:`Signal.propagate`; consumes existing history or
    explicit ``BeatSpec`` entries.
    """

    def __init__(
        self,
        signal: Signal | None = None,
        *,
        layout: LayoutResult,
        graph: CircuitGraph | None = None,
        records: Sequence[PropagationRecord] | None = None,
        beats: Sequence[BeatSpec] | None = None,
        max_beats: int | None = None,
        beat_duration: float = BEAT_DURATION,
        beat_gap: float = BEAT_GAP,
        caption_hold: float = BEAT_CAPTION_HOLD,
        bundle: WaveformBundle | None = None,
        sync_signals: Sequence[Signal] = (),
        panel_spec: WaveformPanelSpec | None = None,
        dim_inactive: bool = False,
        topology: TopologyProjection | None = None,
        label_layer: object | None = None,
        caption_callback: Callable[[BeatSpec, int], None] | None = None,
        waveform_controller: WaveformSegmentController | None = None,
        reveal_tracker: WaveformRevealTracker | None = None,
        label_phase_policy: LabelPhasePolicy | None = None,
        style: TeachingStyle | None = None,
    ) -> None:
        if dim_inactive and topology is None:
            msg = (
                "PropagationSequence(dim_inactive=True) requires topology= "
                "(a TopologyProjection); otherwise dim/restore have no target."
            )
            raise ValueError(msg)
        self._layout = layout
        self._graph = graph
        self._caption_hold = caption_hold
        self._bundle = bundle
        self._sync_signals = tuple(sync_signals)
        self._panel_spec = panel_spec
        self._dim_inactive = dim_inactive
        self._topology = topology
        self._label_layer = label_layer
        self._caption_callback = caption_callback
        self._waveform_controller = waveform_controller
        if self._waveform_controller is None and reveal_tracker is not None:
            self._waveform_controller = WaveformSegmentController(reveal_tracker)
        self._reveal_tracker = (
            self._waveform_controller.tracker if self._waveform_controller is not None else None
        )
        self._label_phase_policy = label_phase_policy or LabelPhasePolicy()
        base_style = style or TeachingStyle()
        self._style = TeachingStyle(
            beat_duration=beat_duration,
            beat_gap=beat_gap,
            caption_crossfade=base_style.caption_crossfade,
            dim_opacity=base_style.dim_opacity,
            pulse_flash_width=base_style.pulse_flash_width,
            wire_flash_width=base_style.wire_flash_width,
            waveform_flash_width=base_style.waveform_flash_width,
            overlay_fade_out=base_style.overlay_fade_out,
            setup_caption_hold_scale=base_style.setup_caption_hold_scale,
            setup_post_hold=base_style.setup_post_hold,
            conclusion_caption_hold_scale=base_style.conclusion_caption_hold_scale,
            conclusion_post_hold=base_style.conclusion_post_hold,
            context_duration_scale=base_style.context_duration_scale,
            context_gap_scale=base_style.context_gap_scale,
            context_pulse_scale=base_style.context_pulse_scale,
            key_duration_scale=base_style.key_duration_scale,
            key_gap_scale=base_style.key_gap_scale,
            key_pulse_scale=base_style.key_pulse_scale,
        )

        if beats is not None:
            specs = list(beats)
        else:
            if signal is None:
                msg = "PropagationSequence requires either 'signal' or 'beats'"
                raise ValueError(msg)
            history = list(records if records is not None else signal.propagation_history)
            specs = [
                BeatSpec(signal=signal, record=record, wave_beat=index)
                for index, record in enumerate(history)
            ]
        if max_beats is not None:
            specs = specs[:max_beats]
        self._beats = tuple(specs)

    @property
    def beat_count(self) -> int:
        return len(self._beats)

    @property
    def beats(self) -> tuple[BeatSpec, ...]:
        return self._beats

    @property
    def waveform_controller(self) -> WaveformSegmentController | None:
        """Controller-first reveal facade used by sequence orchestration."""
        return self._waveform_controller

    def _resolve_transition_profile(self, spec: BeatSpec) -> TransitionProfile:
        if spec.transition_profile is not None:
            return spec.transition_profile
        if spec.emphasis == "context":
            return "setup"
        if spec.emphasis == "key":
            return "conclusion"
        return "default"

    def _resolve_style(self, spec: BeatSpec) -> TeachingStyle:
        base = spec.style or self._style
        profile = self._resolve_transition_profile(spec)
        if profile == "setup":
            resolved = style_for_emphasis(base, "context")
        elif profile == "conclusion":
            resolved = style_for_emphasis(base, "key")
        else:
            resolved = style_for_emphasis(base, spec.emphasis)
        if spec.duration is None:
            return resolved
        return TeachingStyle(
            beat_duration=spec.duration,
            beat_gap=resolved.beat_gap,
            caption_crossfade=resolved.caption_crossfade,
            dim_opacity=resolved.dim_opacity,
            pulse_flash_width=resolved.pulse_flash_width,
            wire_flash_width=resolved.wire_flash_width,
            waveform_flash_width=resolved.waveform_flash_width,
            overlay_fade_out=resolved.overlay_fade_out,
            setup_caption_hold_scale=resolved.setup_caption_hold_scale,
            setup_post_hold=resolved.setup_post_hold,
            conclusion_caption_hold_scale=resolved.conclusion_caption_hold_scale,
            conclusion_post_hold=resolved.conclusion_post_hold,
            context_duration_scale=resolved.context_duration_scale,
            context_gap_scale=resolved.context_gap_scale,
            context_pulse_scale=resolved.context_pulse_scale,
            key_duration_scale=resolved.key_duration_scale,
            key_gap_scale=resolved.key_gap_scale,
            key_pulse_scale=resolved.key_pulse_scale,
        )

    def _caption_settle_duration(self, spec: BeatSpec, style: TeachingStyle) -> float:
        profile = self._resolve_transition_profile(spec)
        caption_len = len((spec.caption or "").strip())
        extra = min(max(caption_len - 12, 0) * 0.003, 0.05)
        if profile == "setup":
            return self._caption_hold * style.setup_caption_hold_scale + extra
        if profile == "conclusion":
            return self._caption_hold * style.conclusion_caption_hold_scale + extra
        return self._caption_hold + extra

    def _post_beat_hold(
        self,
        spec: BeatSpec,
        style: TeachingStyle,
        *,
        caption_len: int = 0,
        reveal_target_count: int = 0,
    ) -> float:
        profile = self._resolve_transition_profile(spec)
        extra = min(max(caption_len - 18, 0) * 0.002, 0.03)
        extra += min(max(reveal_target_count - 1, 0) * 0.015, 0.03)
        if profile == "setup":
            return style.setup_post_hold + extra
        if profile == "conclusion":
            return style.conclusion_post_hold + extra
        return 0.0

    def _label_focus_duration(self, style: TeachingStyle) -> float:
        return max(min(style.beat_duration * 0.18, 0.24), 0.12)

    def _topology_focus_duration(self, spec: BeatSpec, style: TeachingStyle) -> float:
        profile = self._resolve_transition_profile(spec)
        if profile == "conclusion":
            return max(min(style.beat_duration * 0.14, 0.18), 0.09)
        if profile == "setup":
            return max(min(style.beat_duration * 0.1, 0.14), 0.07)
        return max(min(style.beat_duration * 0.08, 0.12), 0.06)

    def _topology_focus_settle_duration(
        self,
        spec: BeatSpec,
        style: TeachingStyle,
        *,
        endpoint_emphasis: bool = False,
        animation_count: int = 1,
    ) -> float:
        profile = self._resolve_transition_profile(spec)
        extra = 0.0
        if endpoint_emphasis:
            extra += 0.015
        if animation_count > 1:
            extra += min((animation_count - 1) * 0.005, 0.01)
        if profile == "conclusion":
            return min(max(min(style.beat_duration * 0.09, 0.1), 0.05) + extra, 0.12)
        if profile == "setup":
            return min(max(min(style.beat_duration * 0.07, 0.08), 0.04) + extra, 0.09)
        return 0.0

    def _build_topology_focus_plan(
        self,
        spec: BeatSpec,
        beat_style: TeachingStyle,
        *,
        profile: TransitionProfile,
    ) -> _TopologyFocusPlan:
        run_time = self._topology_focus_duration(spec, beat_style)
        connection_id = self._resolve_connection_id(
            spec.record.from_pin_id,
            spec.record.to_pin_id,
        )
        wire = wire_path_for_connection(self._layout, connection_id)
        points = oriented_wire_points(
            self._layout,
            wire,
            spec.record.from_pin_id,
            spec.record.to_pin_id,
        )
        signal_color = renderer_theme.color_for_signal_type(spec.signal.signal_type)
        focus_path = path_mobject_from_points(points)
        focus_path.set_stroke(
            color=signal_color,
            width=renderer_theme.WIRE_STROKE_WIDTH * 2.2,
            opacity=1.0,
        )
        animations: list[object] = [
            ShowPassingFlash(
                focus_path,
                time_width=0.7 if profile == "conclusion" else 0.6,
                run_time=run_time,
            )
        ]
        endpoint_emphasis = profile == "conclusion"
        if endpoint_emphasis:
            endpoint = self._layout.pin_positions[spec.record.to_pin_id]
            endpoint_path = path_mobject_from_points(
                (
                    Point2D(endpoint.x - 0.08, endpoint.y),
                    Point2D(endpoint.x + 0.08, endpoint.y),
                )
            )
            endpoint_path.set_stroke(
                color=signal_color,
                width=renderer_theme.WIRE_STROKE_WIDTH * 3.0,
                opacity=1.0,
            )
            animations.append(
                ShowPassingFlash(
                    endpoint_path,
                    time_width=0.85,
                    run_time=run_time,
                )
            )
        return _TopologyFocusPlan(
            run_time=run_time,
            endpoint_emphasis=endpoint_emphasis,
            animations=tuple(animations),
        )

    def _wait_stage(
        self,
        scene: object,
        stage: str,
        spec: BeatSpec,
        *,
        beat_index: int,
        run_time: float,
        purpose: str | None = None,
        **detail: object,
    ) -> None:
        wait_signal_stage(
            scene.wait,
            stage,
            signal_name=spec.signal.name,
            run_time=run_time,
            beat_index=beat_index,
            purpose=purpose,
            record=record_stage,
            **detail,
        )

    def _context_detail(self, context: _BeatContext) -> dict[str, object]:
        record = context.spec.record
        detail: dict[str, object] = {
            "from_pin_id": record.from_pin_id,
            "to_pin_id": record.to_pin_id,
        }
        if context.reveal_time is not None:
            detail["reveal_time"] = context.reveal_time
            detail["reveal_scope"] = context.spec.reveal_scope
        if context.reveal_targets is not None:
            detail["reveal_target_count"] = len(context.reveal_targets)
            detail["reveal_signal_names"] = [
                signal.name for signal, _target in context.reveal_targets
            ]
        return detail

    def _play_wait_plan(
        self,
        scene: object,
        context: _BeatContext,
        plan: _WaitStagePlan | None,
    ) -> None:
        if plan is None or plan.run_time <= 0:
            return
        detail = self._context_detail(context)
        detail.update(plan.detail)
        wait_signal_stage(
            scene.wait,
            plan.stage,
            signal_name=context.signal.name,
            run_time=plan.run_time,
            beat_index=context.index,
            purpose=plan.purpose,
            record=record_stage,
            **detail,
        )

    def _record_context_stage(
        self,
        context: _BeatContext,
        stage: str,
        *,
        run_time: float,
        purpose: str | None = None,
        **detail: object,
    ) -> None:
        common_detail = self._context_detail(context)
        record_signal_stage(
            stage,
            signal_name=context.signal.name,
            run_time=run_time,
            beat_index=context.index,
            purpose=purpose,
            record=record_stage,
            **common_detail,
            **detail,
        )

    def _play_topology_focus(
        self,
        scene: object,
        spec: BeatSpec,
        beat_style: TeachingStyle,
        *,
        beat_index: int,
    ) -> _TopologyFocusPlan | None:
        if self._topology is None:
            return None
        profile = self._resolve_transition_profile(spec)
        if not self._dim_inactive and profile not in {"setup", "conclusion"}:
            return None
        if self._dim_inactive:
            restore_topology(self._topology)
        plan = self._build_topology_focus_plan(spec, beat_style, profile=profile)
        play = getattr(scene, "play", None)
        if callable(play):
            self._record_context_stage(
                _BeatContext(
                    index=beat_index,
                    spec=spec,
                    style=beat_style,
                    transition_profile=profile,
                    reveal_time=None,
                    reveal_targets=None,
                ),
                "sequence.topology_focus",
                run_time=plan.run_time,
                purpose=AnimationPurpose.FOCUS.value,
                transition_profile=profile,
                endpoint_emphasis=plan.endpoint_emphasis,
                animation_count=len(plan.animations),
            )
            play(
                plan.animations[0]
                if len(plan.animations) == 1
                else AnimationGroup(*plan.animations),
                run_time=plan.run_time,
            )
        else:
            self._play_wait_plan(
                scene,
                _BeatContext(
                    index=beat_index,
                    spec=spec,
                    style=beat_style,
                    transition_profile=profile,
                    reveal_time=None,
                    reveal_targets=None,
                ),
                _WaitStagePlan(
                    stage="sequence.topology_focus",
                    run_time=plan.run_time,
                    detail={"transition_profile": profile},
                    purpose=AnimationPurpose.FOCUS.value,
                ),
            )
        return plan

    def _build_label_focus_plan(self, context: _BeatContext) -> _LabelFocusPlan | None:
        if self._topology is None or self._label_layer is None:
            return None
        phase = phase_for_transition_profile(context.transition_profile)
        if phase is None:
            return None
        labels = tuple(
            label
            for label in iter_label_roots(self._label_layer, roles=("component_label", "net_label"))
            if label_allowed_in_phase(label, phase, self._label_phase_policy)
            if not label_visible(label)
        )
        if not labels:
            return None
        run_time = self._label_focus_duration(context.style)
        return _LabelFocusPlan(
            run_time=run_time,
            label_phase=phase,
            labels=labels,
        )

    def _resolve_connection_id(self, from_pin_id: str, to_pin_id: str) -> str:
        if self._graph is not None:
            return connection_id_for_pins(
                self._graph,
                from_pin_id,
                to_pin_id,
            )

        start = self._layout.pin_positions[from_pin_id]
        end = self._layout.pin_positions[to_pin_id]
        pin_keys = {(start.x, start.y), (end.x, end.y)}
        for wire in self._layout.wires:
            if len(wire.points) < 2:
                continue
            endpoints = {
                (wire.points[0].x, wire.points[0].y),
                (wire.points[-1].x, wire.points[-1].y),
            }
            if endpoints == pin_keys:
                return wire.connection_id

        if len(self._layout.wires) == 1:
            return self._layout.wires[0].connection_id

        msg = "unable to resolve topology focus connection (pass graph=)"
        raise ValueError(msg)

    def _label_focus_settle_duration(
        self,
        spec: BeatSpec,
        style: TeachingStyle,
        *,
        label_count: int = 1,
    ) -> float:
        profile = self._resolve_transition_profile(spec)
        if profile not in {"setup", "conclusion"}:
            return 0.0
        base = max(min(style.beat_duration * 0.1, 0.12), 0.06)
        extra = min(max(label_count - 1, 0) * 0.02, 0.04)
        if profile == "conclusion":
            return min(base * 1.25 + extra, 0.16)
        return min(base + extra, 0.14)

    def _build_caption_settle_plan(self, context: _BeatContext) -> _WaitStagePlan | None:
        if self._caption_callback is None or not context.spec.caption or self._caption_hold <= 0:
            return None
        caption_len = len(context.spec.caption.strip())
        return _WaitStagePlan(
            stage="sequence.caption_settle",
            run_time=self._caption_settle_duration(context.spec, context.style),
            detail={
                "transition_profile": context.transition_profile,
                "caption_len": caption_len,
            },
        )

    def _build_topology_focus_settle_plan(
        self,
        context: _BeatContext,
        *,
        topology_focus_plan: _TopologyFocusPlan | None,
    ) -> _WaitStagePlan | None:
        if topology_focus_plan is None:
            return None
        run_time = self._topology_focus_settle_duration(
            context.spec,
            context.style,
            endpoint_emphasis=topology_focus_plan.endpoint_emphasis,
            animation_count=len(topology_focus_plan.animations),
        )
        if run_time <= 0:
            return None
        return _WaitStagePlan(
            stage="sequence.topology_focus_settle",
            run_time=run_time,
            detail={
                "transition_profile": context.transition_profile,
                "endpoint_emphasis": topology_focus_plan.endpoint_emphasis,
                "animation_count": len(topology_focus_plan.animations),
            },
            purpose=AnimationPurpose.FOCUS.value,
        )

    def _build_label_focus_settle_plan(
        self,
        context: _BeatContext,
        *,
        label_focus_plan: _LabelFocusPlan | None,
    ) -> _WaitStagePlan | None:
        if label_focus_plan is None:
            return None
        return _WaitStagePlan(
            stage="sequence.label_focus_settle",
            run_time=self._label_focus_settle_duration(
                context.spec,
                context.style,
                label_count=len(label_focus_plan.labels),
            ),
            detail={
                "transition_profile": context.transition_profile,
                "label_count": len(label_focus_plan.labels),
            },
        )

    def _build_post_hold_plan(self, context: _BeatContext) -> _WaitStagePlan | None:
        caption_len = len((context.spec.caption or "").strip())
        reveal_target_count = len(context.reveal_targets or ())
        return _WaitStagePlan(
            stage="sequence.post_hold",
            run_time=self._post_beat_hold(
                context.spec,
                context.style,
                caption_len=caption_len,
                reveal_target_count=reveal_target_count,
            ),
            detail={
                "transition_profile": context.transition_profile,
                "caption_len": caption_len,
                "reveal_target_count": reveal_target_count,
            },
        )

    def _build_postlude_plan(self, context: _BeatContext) -> _PostludePlan:
        return _PostludePlan(
            post_hold=self._build_post_hold_plan(context),
        )

    def _build_prelude_plan(
        self,
        context: _BeatContext,
        *,
        topology_focus_plan: _TopologyFocusPlan | None,
        label_focus_plan: _LabelFocusPlan | None,
    ) -> _PreludePlan:
        return _PreludePlan(
            topology_focus_enabled=True,
            topology_focus_settle=self._build_topology_focus_settle_plan(
                context,
                topology_focus_plan=topology_focus_plan,
            ),
            caption_settle=self._build_caption_settle_plan(context),
            label_focus_settle=self._build_label_focus_settle_plan(
                context,
                label_focus_plan=label_focus_plan,
            ),
        )

    def _play_label_focus(
        self,
        scene: object,
        context: _BeatContext,
        plan: _LabelFocusPlan | None = None,
    ) -> bool:
        play = getattr(scene, "play", None)
        if not callable(play):
            return False
        plan = plan or self._build_label_focus_plan(context)
        if plan is None:
            return False
        self._record_context_stage(
            context,
            "sequence.label_focus",
            run_time=plan.run_time,
            purpose=AnimationPurpose.FOCUS.value,
            transition_profile=context.transition_profile,
            label_phase=plan.label_phase,
            label_count=len(plan.labels),
        )
        for label in plan.labels:
            set_label_visible(label, True)
            refresh_label_strokes(label, mode="full")
        if len(plan.labels) == 1:
            animation = plan.labels[0].animate.set_opacity(label_target_opacity(plan.labels[0]))
        else:
            animation = LaggedStart(
                *[
                    label.animate.set_opacity(label_target_opacity(label))
                    for label in plan.labels
                ],
                lag_ratio=0.1,
            )
        add = getattr(scene, "add", None)
        if callable(add):
            add(*plan.labels)
        self._label_layer.remove(*plan.labels)
        play(animation, run_time=plan.run_time)
        for label in plan.labels:
            refresh_label_strokes(label, mode="full")
        return True

    def _play_pre_beat_stages(
        self,
        scene: object,
        context: _BeatContext,
    ) -> None:
        spec = context.spec
        topology_focus_plan = self._play_topology_focus(
            scene,
            spec,
            context.style,
            beat_index=context.index,
        )
        pre_caption_plan = self._build_prelude_plan(
            context,
            topology_focus_plan=topology_focus_plan,
            label_focus_plan=None,
        )
        self._play_wait_plan(
            scene,
            context,
            plan=pre_caption_plan.topology_focus_settle,
        )
        if self._caption_callback is not None:
            self._caption_callback(spec, context.index)
        pre_label_focus_plan = self._build_prelude_plan(
            context,
            topology_focus_plan=topology_focus_plan,
            label_focus_plan=None,
        )
        self._play_wait_plan(
            scene,
            context,
            plan=pre_label_focus_plan.caption_settle,
        )
        label_focus_plan = self._build_label_focus_plan(context)
        label_focus_played = (
            self._play_label_focus(scene, context, label_focus_plan)
            if label_focus_plan is not None
            else False
        )
        prelude_plan = self._build_prelude_plan(
            context,
            topology_focus_plan=topology_focus_plan,
            label_focus_plan=label_focus_plan if label_focus_played else None,
        )
        self._play_wait_plan(
            scene,
            context,
            plan=prelude_plan.label_focus_settle,
        )

    def _play_post_beat_stages(
        self,
        scene: object,
        context: _BeatContext,
    ) -> None:
        postlude_plan = self._build_postlude_plan(context)
        self._play_wait_plan(
            scene,
            context,
            plan=postlude_plan.post_hold,
        )

    def _resolve_reveal_payload(
        self,
        spec: BeatSpec,
        *,
        beat_index: int,
    ) -> tuple[float | None, Sequence[tuple[Signal, int]] | None]:
        reveal_time = spec.reveal_time
        reveal_targets = spec.reveal_targets
        if reveal_time is None and reveal_targets is None:
            wave_beat = spec.wave_beat if spec.wave_beat is not None else beat_index
            reveal_targets = ((spec.signal, wave_beat),)
        return reveal_time, reveal_targets

    def _build_beat_context(self, spec: BeatSpec, *, beat_index: int) -> _BeatContext:
        reveal_time, reveal_targets = self._resolve_reveal_payload(spec, beat_index=beat_index)
        return _BeatContext(
            index=beat_index,
            spec=spec,
            style=self._resolve_style(spec),
            transition_profile=self._resolve_transition_profile(spec),
            reveal_time=reveal_time,
            reveal_targets=tuple(reveal_targets) if reveal_targets is not None else None,
        )

    def _play_beat_body(
        self,
        scene: object,
        context: _BeatContext,
    ) -> None:
        spec = context.spec
        try:
            play_propagation_beat(
                scene,
                spec.signal,
                layout=self._layout,
                graph=self._graph,
                record=spec.record,
                duration=context.style.beat_duration,
                bundle=self._bundle,
                signals=self._sync_signals,
                panel_spec=self._panel_spec,
                beat=context.beat,
                beat_index=context.index,
                waveform_controller=self._waveform_controller,
                reveal_targets=context.reveal_targets,
                reveal_time=context.reveal_time,
                reveal_scope=spec.reveal_scope,
                wire_pulse=spec.wire_pulse,
                style=context.style,
                timing_mode=spec.timing_mode,
            )
        except Exception as exc:
            if isinstance(exc, BeatAnimationError):
                raise
            msg = f"beat animation failed for signal {spec.signal.name!r}"
            raise BeatAnimationError(
                msg,
                beat_index=context.index,
                signal_name=spec.signal.name,
                stage="beat.play",
                cause=exc,
            ) from exc

    def _record_beat_start(self, context: _BeatContext) -> None:
        self._record_context_stage(
            context,
            "sequence.beat_start",
            run_time=context.style.beat_duration,
            transition_profile=context.transition_profile,
            wire_pulse=context.spec.wire_pulse,
            timing_mode=context.spec.timing_mode,
            caption_len=len(context.spec.caption or ""),
        )

    def _record_beat_end(self, context: _BeatContext) -> None:
        self._record_context_stage(
            context,
            "sequence.beat_end",
            run_time=context.style.beat_duration,
        )

    def play(self, scene: object) -> None:
        scene = require_scene_methods(scene, require_play=False, require_wait=True)

        for index, spec in enumerate(self._beats):
            context = self._build_beat_context(spec, beat_index=index)
            self._record_beat_start(context)
            maybe_snapshot_stage(scene, f"beat_{index:02d}_before")

            self._play_pre_beat_stages(scene, context)
            self._play_beat_body(scene, context)

            maybe_snapshot_stage(scene, f"beat_{index:02d}_after")
            self._record_beat_end(context)

            self._play_post_beat_stages(scene, context)

            if index < len(self._beats) - 1:
                scene.wait(context.style.beat_gap)
                if self._dim_inactive and self._topology is not None:
                    dim_topology(self._topology, opacity=context.style.dim_opacity)
