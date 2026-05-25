"""Apply a layout preset to ``LayoutEngine.layout`` with optional fields."""

from __future__ import annotations

from collections.abc import Mapping

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.engine import LayoutEngine
from manim_engineering.layout.types import LayoutResult


def layout_from_preset(
    engine: LayoutEngine,
    graph: CircuitGraph,
    elements: Mapping[str, CircuitElement],
    preset,
) -> LayoutResult:
    """Run ``LayoutEngine.layout`` using fields exposed on a preset dataclass."""
    kwargs: dict = {
        "placement_overrides": preset.overrides,
    }
    if hasattr(preset, "orientation_overrides"):
        kwargs["orientation_overrides"] = preset.orientation_overrides
    if hasattr(preset, "text_overrides"):
        kwargs["text_overrides"] = preset.text_overrides
    if hasattr(preset, "label_mode_overrides"):
        kwargs["label_mode_overrides"] = preset.label_mode_overrides
    if hasattr(preset, "net_waypoints"):
        kwargs["net_waypoints"] = preset.net_waypoints
    if hasattr(preset, "connection_waypoints"):
        kwargs["connection_waypoints"] = preset.connection_waypoints
    return engine.layout(graph, elements, **kwargs)


__all__ = ["layout_from_preset"]
