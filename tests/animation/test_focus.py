"""Focus overlays: dim/restore must round-trip without point mutation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("manim")

from manim import VGroup, VMobject

from manim_engineering.animation.focus import (
    DEFAULT_DIM_OPACITY,
    dim_topology,
    restore_topology,
)
from manim_engineering.renderers.minimal.immutable import TopologyProjection


def _filled_vmob() -> VMobject:
    mob = VMobject()
    mob.set_points_as_corners([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]])
    mob.set_stroke(width=2.0, opacity=1.0)
    return mob


def _projection() -> TopologyProjection:
    components = VGroup(_filled_vmob(), _filled_vmob())
    wires = VGroup(_filled_vmob())
    return TopologyProjection(components=components, wires=wires, n_components=2)


def test_dim_topology_lowers_stroke_opacity() -> None:
    projection = _projection()
    dim_topology(projection)
    for mob in projection.components.submobjects:
        assert mob.get_stroke_opacity() == pytest.approx(DEFAULT_DIM_OPACITY)


def test_restore_topology_brings_back_full_stroke_opacity() -> None:
    projection = _projection()
    dim_topology(projection)
    restore_topology(projection)
    for mob in projection.components.submobjects:
        assert mob.get_stroke_opacity() == pytest.approx(1.0)


def test_propagation_sequence_dim_inactive_restores_between_beats() -> None:
    """Sequence with ``dim_inactive=True`` must restore at the start of every beat."""
    from manim_engineering.animation import BEAT_DURATION, BeatSpec, PropagationSequence
    from manim_engineering.components import Resistor
    from manim_engineering.core import CircuitGraph, SignalType
    from manim_engineering.layout import LayoutEngine
    from manim_engineering.semantic import LogicLevel, LogicState, Signal

    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="edge", signal_type=SignalType.DIGITAL, value=LogicState(level=LogicLevel.LOW)
    )
    for _ in range(2):
        signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
        signal.value = LogicState(
            level=LogicLevel.HIGH if signal.value.level == LogicLevel.LOW else LogicLevel.LOW
        )

    projection = _projection()
    beats = tuple(
        BeatSpec(signal=signal, record=rec, wave_beat=i)
        for i, rec in enumerate(signal.propagation_history[:2])
    )

    class _Scene:
        def __init__(self) -> None:
            self.events: list[str] = []

        def add(self, *args, **kwargs) -> None:
            self.events.append("add")

        def remove(self, *args, **kwargs) -> None:
            self.events.append("remove")

        def play(self, *args, **kwargs) -> None:
            self.events.append("play")

        def wait(self, *args, **kwargs) -> None:
            self.events.append("wait")

    seq = PropagationSequence(
        layout=layout,
        graph=graph,
        beats=beats,
        beat_duration=BEAT_DURATION,
        dim_inactive=True,
        topology=projection,
    )

    with patch(
        "manim_engineering.animation.propagation_sequence.restore_topology",
    ) as restore:
        seq.play(_Scene())
    assert restore.call_count == len(beats)


def test_dim_topology_does_not_mutate_points() -> None:
    """Opacity-only dim must leave the geometry arrays untouched."""
    projection = _projection()
    component_points_before = [
        mob.get_all_points().copy() for mob in projection.components.submobjects
    ]
    wire_points_before = [mob.get_all_points().copy() for mob in projection.wires.submobjects]

    dim_topology(projection)

    for before, mob in zip(component_points_before, projection.components.submobjects, strict=True):
        assert mob.get_all_points().shape == before.shape
        assert (mob.get_all_points() == before).all()
    for before, mob in zip(wire_points_before, projection.wires.submobjects, strict=True):
        assert (mob.get_all_points() == before).all()
