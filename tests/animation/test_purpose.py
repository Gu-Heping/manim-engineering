"""Animation purpose enum contract."""

from __future__ import annotations

from manim_engineering.animation import AnimationPurpose


def test_animation_purpose_values() -> None:
    assert AnimationPurpose.PROPAGATION.value == "propagation"
    assert AnimationPurpose.TIMING.value == "timing"
    assert AnimationPurpose.FOCUS.value == "focus"
    assert AnimationPurpose.TRANSITION.value == "transition"


def test_animation_purpose_is_str_enum() -> None:
    assert str(AnimationPurpose.PROPAGATION) == "AnimationPurpose.PROPAGATION"
