"""Shared z-index constants for animation overlays.

A single source of truth so beat orchestration, SignalFlow, WaveformSync, and
scene HUD never disagree about layering. Lower numbers draw farther back.
"""

from __future__ import annotations

# Static topology (components, wires, waveform panel) lives at default 0/1.
TIMING_Z_INDEX = 2
PROPAGATION_Z_INDEX = 3
PULSE_Z_INDEX = 4
HUD_Z_INDEX = 10
