"""Minimal animation primitive registry."""

from __future__ import annotations

import pytest

from manim_engineering.animation import (
    AnalogRamp,
    LogicTransition,
    SignalFlow,
    VoltagePulse,
    WaveformSync,
    get_primitive,
    primitive_registry_view,
    registered_primitives,
)


def test_signal_flow_registered() -> None:
    assert get_primitive("signal_flow") is SignalFlow
    assert "signal_flow" in registered_primitives()


def test_analog_ramp_registered() -> None:
    assert get_primitive("analog_ramp") is AnalogRamp
    assert "analog_ramp" in registered_primitives()


def test_waveform_sync_registered() -> None:
    assert get_primitive("waveform_sync") is WaveformSync
    assert "waveform_sync" in registered_primitives()


def test_voltage_pulse_registered() -> None:
    assert get_primitive("voltage_pulse") is VoltagePulse
    assert "voltage_pulse" in registered_primitives()


def test_logic_transition_registered() -> None:
    assert get_primitive("logic_transition") is LogicTransition
    assert "logic_transition" in registered_primitives()


def test_unknown_primitive_error_names_missing_key() -> None:
    with pytest.raises(KeyError, match="unknown animation primitive"):
        get_primitive("not_registered")


def test_primitive_registry_view_is_read_only_live_view() -> None:
    view = primitive_registry_view()
    assert view["signal_flow"] is SignalFlow
    with pytest.raises(TypeError):
        view["new"] = SignalFlow  # type: ignore[index]


def test_primitive_registry_view_reflects_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    from manim_engineering.animation import registry as registry_module
    from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
    from manim_engineering.animation.purpose import AnimationPurpose
    from manim_engineering.animation.registry import register_primitive

    snapshot = dict(registry_module._REGISTRY)
    monkeypatch.setattr(registry_module, "_REGISTRY", snapshot)

    class _ProbePrimitive(AnimationPrimitive["_ProbePrimitive"]):
        purpose = AnimationPurpose.FOCUS

        def build(self) -> AnimationPlan:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

    name = "_test_probe_primitive_do_not_use"
    register_primitive(name, _ProbePrimitive)
    assert primitive_registry_view()[name] is _ProbePrimitive
    assert name in registered_primitives()


def test_register_primitive_rejects_duplicate_name_with_different_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from manim_engineering.animation import registry as registry_module
    from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
    from manim_engineering.animation.purpose import AnimationPurpose
    from manim_engineering.animation.registry import register_primitive

    snapshot = dict(registry_module._REGISTRY)
    monkeypatch.setattr(registry_module, "_REGISTRY", snapshot)

    class _FirstPrimitive(AnimationPrimitive["_FirstPrimitive"]):
        purpose = AnimationPurpose.FOCUS

        def build(self) -> AnimationPlan:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

    class _SecondPrimitive(AnimationPrimitive["_SecondPrimitive"]):
        purpose = AnimationPurpose.FOCUS

        def build(self) -> AnimationPlan:
            return AnimationPlan(overlays=(), animations=(), run_time=self.duration)

    name = "_test_duplicate_primitive_do_not_use"
    register_primitive(name, _FirstPrimitive)
    assert register_primitive(name, _FirstPrimitive) is _FirstPrimitive
    with pytest.raises(ValueError, match="primitive already registered"):
        register_primitive(name, _SecondPrimitive)
