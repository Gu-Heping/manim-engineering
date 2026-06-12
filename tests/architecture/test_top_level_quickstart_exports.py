from __future__ import annotations

import importlib
import importlib.util
import sys
from typing import get_args

import pytest


def test_top_level_exports_cover_task_level_diagram_path() -> None:
    import manim_engineering as me

    assert me.CircuitGraph is not None
    assert me.LayoutEngine is not None
    assert me.Resistor is not None
    assert me.Ground is not None
    assert me.InputDriver is not None
    assert me.NMOSDepletion is not None
    assert me.PMOSDepletion is not None
    assert me.SignalType is not None
    assert me.SPIMaster is not None
    assert me.SPISlave is not None
    assert me.TextPlacementOverride is not None
    assert me.UARTPort is not None
    assert me.build_circuit is not None
    assert me.layout_circuit is not None
    assert me.render_circuit_diagram is not None
    assert me.export_circuit_preview is not None


def test_top_level_init_does_not_eagerly_import_optional_renderer_stack() -> None:
    sys.modules.pop("manim_engineering", None)
    sys.modules.pop("manim_engineering.renderers", None)
    sys.modules.pop("manim_engineering.renderers.minimal", None)

    me = importlib.import_module("manim_engineering")

    assert "manim_engineering.renderers.minimal" not in sys.modules

    if importlib.util.find_spec("manim") is not None:
        assert me.ManimRenderer is not None
        assert "manim_engineering.renderers.minimal" in sys.modules


def test_all_exports_are_importable() -> None:
    import manim_engineering as me

    for name in me.__all__:
        assert getattr(me, name, None) is not None, f"__all__ member {name!r} not importable"


def test_top_level_module_hides_optional_renderer_symbols_when_manim_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sys.modules.pop("manim_engineering", None)
    sys.modules.pop("manim_engineering.renderers", None)
    sys.modules.pop("manim_engineering.renderers.minimal", None)

    original_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, package: str | None = None):
        if name == "manim":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    me = importlib.import_module("manim_engineering")

    assert "ManimRenderer" not in me.__all__
    with pytest.raises(AttributeError):
        _ = me.ManimRenderer


def test_layout_package_reexports_label_and_routing_types() -> None:
    from manim_engineering.layout import (
        LabelPlacementMode,
        RoutingIssueKind,
        RoutingIssueSeverity,
        RoutingSegmentAxis,
    )

    assert LabelPlacementMode.AUTO.value == "auto"
    assert get_args(RoutingIssueSeverity) == ("cosmetic", "ambiguous", "blocking")
    assert get_args(RoutingIssueKind)
    assert get_args(RoutingSegmentAxis)
