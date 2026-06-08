from __future__ import annotations

import importlib
import importlib.util
import sys
from typing import get_args


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
        if name == "ManimRenderer" and importlib.util.find_spec("manim") is None:
            continue
        assert getattr(me, name, None) is not None, f"__all__ member {name!r} not importable"


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
