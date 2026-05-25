"""Typed exceptions for the waveform layer."""

from manim_engineering.core.exceptions import CoreError


class WaveformError(CoreError):
    """Base exception for waveform-layer errors."""


class InvalidWaveformParamsError(WaveformError):
    """Raised when RC / trace parameter contracts are violated."""
