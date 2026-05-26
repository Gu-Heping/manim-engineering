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

from manim_engineering.animation.beat import play_propagation_beat
from manim_engineering.animation.focus import dim_topology, restore_topology
from manim_engineering.animation.pacing import BEAT_CAPTION_HOLD, BEAT_DURATION, BEAT_GAP
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle


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
        caption_callback: Callable[[BeatSpec, int], None] | None = None,
        reveal_tracker: WaveformRevealTracker | None = None,
    ) -> None:
        if dim_inactive and topology is None:
            # Silently no-op'ing here was the root cause of "我以为开了 dim
            # 但是看不出来" — make the misconfiguration loud.
            msg = (
                "PropagationSequence(dim_inactive=True) requires topology= "
                "(a TopologyProjection); otherwise dim/restore have no target."
            )
            raise ValueError(msg)
        self._layout = layout
        self._graph = graph
        self._beat_duration = beat_duration
        self._beat_gap = beat_gap
        self._caption_hold = caption_hold
        self._bundle = bundle
        self._sync_signals = tuple(sync_signals)
        self._panel_spec = panel_spec
        self._dim_inactive = dim_inactive
        self._topology = topology
        self._caption_callback = caption_callback
        self._reveal_tracker = reveal_tracker

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

    def play(self, scene: object) -> None:
        scene = require_scene_methods(scene, require_play=False, require_wait=True)

        for index, spec in enumerate(self._beats):
            if self._dim_inactive and self._topology is not None:
                restore_topology(self._topology)
            if self._caption_callback is not None:
                self._caption_callback(spec, index)
                # Hold the caption briefly so the viewer reads *before* the
                # pulse fires. Skipped when no caption (e.g. clock_data demo).
                if spec.caption and self._caption_hold > 0:
                    scene.wait(self._caption_hold)
            reveal_time = spec.reveal_time
            reveal_targets = spec.reveal_targets
            if reveal_time is None:
                if reveal_targets is None:
                    wave_beat = spec.wave_beat if spec.wave_beat is not None else index
                    reveal_targets = ((spec.signal, wave_beat),)
            beat_duration = spec.duration if spec.duration is not None else self._beat_duration
            play_propagation_beat(
                scene,
                spec.signal,
                layout=self._layout,
                graph=self._graph,
                record=spec.record,
                duration=beat_duration,
                bundle=self._bundle,
                signals=self._sync_signals,
                panel_spec=self._panel_spec,
                beat=spec.wave_beat if spec.wave_beat is not None else index,
                reveal_tracker=self._reveal_tracker,
                reveal_targets=reveal_targets,
                reveal_time=reveal_time,
                reveal_scope=spec.reveal_scope,
                wire_pulse=spec.wire_pulse,
            )
            if index < len(self._beats) - 1:
                scene.wait(self._beat_gap)
                if self._dim_inactive and self._topology is not None:
                    dim_topology(self._topology)
