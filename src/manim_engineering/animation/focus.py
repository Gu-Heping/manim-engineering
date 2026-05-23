"""Focus overlays: dim inactive topology without mutating point geometry."""

from __future__ import annotations

from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    LabelRefreshMode,
    refresh_label_strokes,
)

DEFAULT_DIM_OPACITY = 0.38


def dim_topology(topology: TopologyProjection, *, opacity: float = DEFAULT_DIM_OPACITY) -> None:
    """Reduce contrast on static circuit geometry (opacity only, not point mutation)."""
    topology.components.set_opacity(opacity)
    topology.wires.set_opacity(opacity)
    refresh_label_strokes(topology.components, mode="stroke_only")


def restore_topology(topology: TopologyProjection) -> None:
    """Restore full opacity after a focus beat."""
    topology.components.set_opacity(1.0)
    topology.wires.set_opacity(1.0)
    refresh_label_strokes(topology.components, mode="full")


def normalize_topology_labels(
    topology: TopologyProjection,
    *,
    waveform_panel: object | None = None,
    mode: LabelRefreshMode = "full",
) -> None:
    """Reconcile pin/trace labels after opacity animations (``FadeIn``, ``set_opacity``).

    Pass ``waveform_panel`` when intro also animates the timing panel.
    Use ``mode='stroke_only'`` only when labels should keep inherited dim opacity.
    """
    refresh_label_strokes(topology.components, mode=mode)
    if waveform_panel is not None:
        refresh_label_strokes(waveform_panel, mode=mode)  # type: ignore[arg-type]
