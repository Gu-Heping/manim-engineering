"""SignalFlow pulse color and size from semantic metadata."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import GREEN_C, YELLOW_C

from manim_engineering.animation import SignalFlow
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import theme
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _propagated(signal_type: SignalType) -> tuple[object, Signal]:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="s",
        signal_type=signal_type,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return layout, signal


def test_pulse_color_follows_clock_signal_type() -> None:
    layout, signal = _propagated(SignalType.CLOCK)
    plan = SignalFlow(signal, layout=layout).build()
    pulse = plan.overlays[0]
    assert pulse.get_color() == YELLOW_C


def test_pulse_color_follows_data_signal_type() -> None:
    layout, signal = _propagated(SignalType.DATA)
    plan = SignalFlow(signal, layout=layout).build()
    pulse = plan.overlays[0]
    assert pulse.get_color() == GREEN_C


def test_pulse_radius_within_theme_bounds() -> None:
    layout, signal = _propagated(SignalType.SIGNAL)
    plan = SignalFlow(signal, layout=layout).build()
    pulse = plan.overlays[0]
    radius = float(pulse.radius)
    assert theme.PULSE_RADIUS_MIN <= radius <= theme.PULSE_RADIUS_MAX
