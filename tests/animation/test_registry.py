"""Minimal animation primitive registry."""

from __future__ import annotations

from manim_engineering.animation import SignalFlow, get_primitive, registered_primitives


def test_signal_flow_registered() -> None:
    assert get_primitive("signal_flow") is SignalFlow
    assert "signal_flow" in registered_primitives()
