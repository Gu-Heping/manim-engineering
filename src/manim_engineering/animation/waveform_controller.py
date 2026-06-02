"""Thin facade over :class:`WaveformRevealTracker` for beat-time segment plans."""

from __future__ import annotations

from manim_engineering.animation.waveform_reveal import SegmentRevealPlan, WaveformRevealTracker
from manim_engineering.semantic.signal import Signal


class WaveformSegmentController:
    """Stable-append waveform reveal; beats consume plans instead of mutating geometry inline."""

    def __init__(self, tracker: WaveformRevealTracker) -> None:
        self._tracker = tracker

    @property
    def tracker(self) -> WaveformRevealTracker:
        return self._tracker

    def sync_idle_baselines(self, signal_names: set[str] | frozenset[str] | None = None) -> None:
        self._tracker.sync_idle_baselines(signal_names)

    def revealed_time_for(self, signal_name: str) -> float:
        return self._tracker.revealed_time_for(signal_name)

    def plan_reveal_for_beat(self, signal: Signal, target_beat: int) -> SegmentRevealPlan:
        return self._tracker.append_through_beat(signal, target_beat)

    def plan_reveal_for_time(self, reveal_time: float) -> tuple[SegmentRevealPlan, ...]:
        return self._tracker.append_through_time(reveal_time)

    def plan_reveal_for_time_on_signal(
        self,
        signal_name: str,
        reveal_time: float,
    ) -> SegmentRevealPlan:
        return self._tracker.append_through_time_for(signal_name, reveal_time)

    def finalize_hold_to_panel(self) -> tuple[object, ...]:
        return self._tracker.finalize_hold_to_panel()
