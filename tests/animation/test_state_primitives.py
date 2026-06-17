"""VoltagePulse and LogicTransition local emphasis primitives."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, Circle, Rectangle

from manim_engineering.animation import (
    PULSE_Z_INDEX,
    TIMING_Z_INDEX,
    LogicTransition,
    VoltagePulse,
)
from manim_engineering.animation.purpose import AnimationPurpose


def test_voltage_pulse_builds_timing_ring_plan() -> None:
    pulse = VoltagePulse(center=(1.0, 2.0, 0.0), radius=0.25, duration=0.7)
    plan = pulse.build()

    assert pulse.purpose is AnimationPurpose.TIMING
    assert plan.run_time == pytest.approx(0.7)
    assert len(plan.overlays) == 1
    assert isinstance(plan.overlays[0], Circle)
    assert plan.overlays[0].z_index == TIMING_Z_INDEX
    assert plan.overlays[0].get_center()[0] == pytest.approx(1.0)
    assert plan.overlays[0].get_center()[1] == pytest.approx(2.0)
    assert isinstance(plan.animations[0], AnimationGroup)


def test_logic_transition_builds_transition_marker_plan() -> None:
    transition = LogicTransition(center=(-1.0, 0.5, 0.0), width=0.6, height=0.3)
    plan = transition.build()

    assert transition.purpose is AnimationPurpose.TRANSITION
    assert len(plan.overlays) == 1
    assert isinstance(plan.overlays[0], Rectangle)
    assert plan.overlays[0].z_index == PULSE_Z_INDEX
    assert plan.overlays[0].width == pytest.approx(0.6)
    assert plan.overlays[0].height == pytest.approx(0.3)
    assert plan.overlays[0].get_center()[0] == pytest.approx(-1.0)
    assert plan.overlays[0].get_center()[1] == pytest.approx(0.5)
    assert isinstance(plan.animations[0], AnimationGroup)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"radius": 0.0},
        {"stroke_width": 0.0},
        {"center": (1.0,)},
    ],
)
def test_voltage_pulse_validates_geometry(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        VoltagePulse(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": 0.0},
        {"height": 0.0},
        {"stroke_width": 0.0},
        {"center": (1.0,)},
    ],
)
def test_logic_transition_validates_geometry(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        LogicTransition(**kwargs)
