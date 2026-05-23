"""SignalFlow sequencing and duration without full video render."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import MoveAlongPath

from manim_engineering.animation import (
    DEFAULT_PROPAGATION_DURATION,
    AnimationPurpose,
    SignalFlow,
)
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _propagated_fixture() -> tuple[CircuitGraph, dict[str, Resistor], object, Signal]:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    signal = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return graph, elements, layout, signal


def test_signal_flow_purpose_is_propagation() -> None:
    assert SignalFlow.purpose == AnimationPurpose.PROPAGATION


def test_signal_flow_default_duration() -> None:
    _, _, layout, signal = _propagated_fixture()
    flow = SignalFlow(signal, layout=layout)
    assert flow.duration == DEFAULT_PROPAGATION_DURATION


def test_signal_flow_set_duration_updates_plan() -> None:
    _, _, layout, signal = _propagated_fixture()
    flow = SignalFlow(signal, layout=layout).set_duration(1.25)
    plan = flow.build()
    assert plan.run_time == pytest.approx(1.25)
    assert flow.duration == pytest.approx(1.25)


def test_signal_flow_build_produces_pulse_and_motion() -> None:
    graph, _, layout, signal = _propagated_fixture()
    plan = SignalFlow(signal, layout=layout, graph=graph).build()
    assert len(plan.overlays) == 1
    assert len(plan.animations) >= 1
    motion = plan.animations[0]
    if hasattr(motion, "animations"):
        motion = motion.animations[0]
    assert isinstance(motion, MoveAlongPath)


def test_signal_flow_requires_layout() -> None:
    _, _, _, signal = _propagated_fixture()
    flow = SignalFlow(signal)
    with pytest.raises(ValueError, match="layout"):
        flow.build()


def test_signal_flow_requires_history_when_no_record() -> None:
    signal = Signal(name="empty", signal_type=SignalType.DIGITAL)
    with pytest.raises(ValueError, match="PropagationRecord"):
        SignalFlow(signal).resolved_record()


class _RecordingScene:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.played: list[tuple[object, ...]] = []
        self.run_times: list[float | None] = []

    def add(self, *mobjects: object) -> None:
        self.added.extend(mobjects)

    def play(self, *animations: object, run_time: float | None = None) -> None:
        self.played.append(animations)
        self.run_times.append(run_time)


def test_signal_flow_play_delegates_to_scene() -> None:
    graph, _, layout, signal = _propagated_fixture()
    scene = _RecordingScene()
    SignalFlow(signal, layout=layout, graph=graph, duration=0.9).play(scene)
    assert len(scene.added) == 2
    assert any(getattr(m, "submobjects", None) for m in scene.added)
    assert len(scene.played) == 1
    assert scene.run_times[0] == pytest.approx(0.9)
