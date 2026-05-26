"""Structured errors for animation beat failures."""

from __future__ import annotations


class BeatAnimationError(RuntimeError):
    """Wrap a beat-stage failure with sequence context for debugging."""

    def __init__(
        self,
        message: str,
        *,
        beat_index: int | None,
        signal_name: str | None,
        stage: str,
        cause: BaseException,
    ) -> None:
        self.beat_index = beat_index
        self.signal_name = signal_name
        self.stage = stage
        self.cause = cause
        context = f"stage={stage}"
        if beat_index is not None:
            context += f", beat_index={beat_index}"
        if signal_name is not None:
            context += f", signal={signal_name!r}"
        super().__init__(f"{message} ({context})")
