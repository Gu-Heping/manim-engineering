"""Preset dataclass label/orientation API and layout_from_preset wiring."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.presets import (
    CmosInverterLayoutPreset,
    NpnCeLayoutPreset,
    OpampLayoutPreset,
    ZenerRegulatorLayoutPreset,
    layout_from_preset,
)
from manim_engineering.layout.types import Point2D, TextPlacementOverride


@pytest.mark.parametrize(
    "preset_cls",
    (
        CmosInverterLayoutPreset,
        NpnCeLayoutPreset,
        OpampLayoutPreset,
        ZenerRegulatorLayoutPreset,
    ),
)
def test_preset_exposes_label_override_fields(preset_cls) -> None:
    fields = {item.name for item in preset_cls.__dataclass_fields__.values()}
    assert "text_overrides" in fields
    assert "label_mode_overrides" in fields
    assert "orientation_overrides" in fields


def test_layout_from_preset_applies_text_overrides() -> None:
    @dataclass(frozen=True)
    class _FakePreset:
        overrides: dict[str, Point2D]
        orientation_overrides: dict = field(default_factory=dict)
        text_overrides: dict[str, tuple[TextPlacementOverride, ...]] = field(
            default_factory=dict
        )
        label_mode_overrides: dict = field(default_factory=dict)

    graph = CircuitGraph()
    resistor = Resistor("r1", label="R1")
    resistor.attach_to(graph)
    elements = {resistor.element_id: resistor}
    manual = Point2D(3.0, 4.0)
    preset = _FakePreset(
        overrides={resistor.element_id: Point2D(0.0, 0.0)},
        text_overrides={
            resistor.element_id: (
                TextPlacementOverride(role="component_label", world=manual),
            )
        },
    )
    layout = layout_from_preset(LayoutEngine(), graph, elements, preset)
    placement = next(item for item in layout.placements if item.element_id == "r1")
    assert placement.text_overrides == preset.text_overrides[resistor.element_id]
    assert placement.text_overrides[0].world == manual
