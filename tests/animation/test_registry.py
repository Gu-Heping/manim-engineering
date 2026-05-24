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
