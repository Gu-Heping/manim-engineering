"""Minimal animation primitive registry."""

from __future__ import annotations

import pytest

from manim_engineering.animation import (
    SignalFlow,
    get_primitive,
    primitive_registry_view,
    registered_primitives,
)


def test_signal_flow_registered() -> None:
    assert get_primitive("signal_flow") is SignalFlow
    assert "signal_flow" in registered_primitives()


def test_primitive_registry_view_is_read_only_live_view() -> None:
    view = primitive_registry_view()
    assert view["signal_flow"] is SignalFlow
    with pytest.raises(TypeError):
        view["new"] = SignalFlow  # type: ignore[index]


def test_primitive_registry_view_reflects_registration() -> None:
    from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
    from manim_engineering.animation.purpose import AnimationPurpose
    from manim_engineering.animation.registry import register_primitive

    class _ProbePrimitive(AnimationPrimitive["_ProbePrimitive"]):
        purpose = AnimationPurpose.FOCUS

        def build(self) -> AnimationPlan:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

    name = "_test_probe_primitive_do_not_use"
    register_primitive(name, _ProbePrimitive)
    assert primitive_registry_view()[name] is _ProbePrimitive
    assert name in registered_primitives()
