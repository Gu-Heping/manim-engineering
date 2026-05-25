"""Focus overlays: dim inactive topology without mutating point geometry."""

from __future__ import annotations

from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    LabelRefreshMode,
    apply_label_opacity,
    apply_symbol_opacity,
    normalize_stroke_only_geometry,
    refresh_label_strokes,
)

DEFAULT_DIM_OPACITY = 0.38


def dim_topology(topology: TopologyProjection, *, opacity: float = DEFAULT_DIM_OPACITY) -> None:
    """Reduce contrast on static circuit geometry (stroke/fill opacity only)."""

    apply_symbol_opacity(topology.components, opacity)

    apply_symbol_opacity(topology.wires, opacity)

    apply_label_opacity(topology.components, opacity)

    refresh_label_strokes(topology.components, mode="stroke_only")


def restore_topology(topology: TopologyProjection) -> None:
    """Restore full contrast after a focus beat without ``VGroup.set_opacity``."""

    apply_symbol_opacity(topology.components, 1.0)

    apply_symbol_opacity(topology.wires, 1.0)

    apply_label_opacity(topology.components, 1.0)

    normalize_stroke_only_geometry(topology.components)

    normalize_stroke_only_geometry(topology.wires)

    refresh_label_strokes(topology.components, mode="full")


def normalize_topology_labels(
    topology: TopologyProjection,
    *,
    waveform_panel: object | None = None,
    mode: LabelRefreshMode = "full",
) -> None:
    """Reconcile pin/trace labels after opacity animations (``FadeIn``, ``Create``).

    Pass ``waveform_panel`` when intro also animates the timing panel.

    Use ``mode='stroke_only'`` only when labels should keep inherited dim opacity.

    """

    normalize_stroke_only_geometry(topology.components)

    normalize_stroke_only_geometry(topology.wires)

    refresh_label_strokes(topology.components, mode=mode)

    if waveform_panel is not None:
        normalize_stroke_only_geometry(waveform_panel)  # type: ignore[arg-type]
        refresh_label_strokes(waveform_panel, mode=mode)  # type: ignore[arg-type]
