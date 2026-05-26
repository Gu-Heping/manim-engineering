"""Teaching-scene intro staging: stroke-first topology reveal without VGroup opacity."""

from __future__ import annotations

from manim import Animation, Create, LaggedStart, VGroup

from manim_engineering.animation.focus import normalize_topology_labels
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.trace import record_stage
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    apply_symbol_opacity,
    hide_labels,
    iter_symbol_strokes,
    prepare_stroke_reveal,
    show_labels,
)


def _lagged_creates(mobjects: tuple[object, ...], run_time: float, lag_ratio: float) -> Animation:
    if not mobjects:
        from manim import Wait

        return Wait(run_time=run_time)
    if len(mobjects) == 1:
        return Create(mobjects[0], run_time=run_time)
    return LaggedStart(
        *[Create(mob, run_time=run_time) for mob in mobjects],
        lag_ratio=lag_ratio,
    )


def play_topology_intro(
    scene: object,
    topology: TopologyProjection,
    waveform_panel: VGroup,
    content: VGroup,
    *,
    components_run_time: float,
    wires_run_time: float,
    panel_run_time: float,
    lag_ratio: float,
    total_run_time: float,
    create_lag_ratio: float = 0.1,
) -> None:
    """Reveal circuit bodies with ``Create`` on strokes; panel traces use the same path.

    Avoids ``FadeIn`` / ``set_opacity`` on heterogeneous ``topology.components`` groups,
    which activates default white fill on Manim ``Line`` symbols (resistor zig-zag bug).
    The waveform panel uses ``prepare_stroke_reveal`` + ``Create`` on trace strokes instead
    of ``VGroup.set_opacity(0)`` + ``FadeIn``.
    """
    scene = require_scene_methods(scene, require_play=True, require_add=True)

    component_strokes = iter_symbol_strokes(topology.components)
    wire_strokes = iter_symbol_strokes(topology.wires)
    panel_strokes = iter_symbol_strokes(waveform_panel)
    prepare_stroke_reveal(component_strokes)
    prepare_stroke_reveal(wire_strokes)
    prepare_stroke_reveal(panel_strokes)

    hide_labels(topology.components)
    hide_labels(waveform_panel)
    scene.add(content)
    scene.play(
        LaggedStart(
            _lagged_creates(component_strokes, components_run_time, create_lag_ratio),
            _lagged_creates(wire_strokes, wires_run_time, create_lag_ratio),
            _lagged_creates(panel_strokes, panel_run_time, create_lag_ratio),
            lag_ratio=lag_ratio,
        ),
        run_time=total_run_time,
    )
    apply_symbol_opacity(topology.components, 1.0)
    apply_symbol_opacity(topology.wires, 1.0)
    apply_symbol_opacity(waveform_panel, 1.0)
    show_labels(topology.components)
    show_labels(waveform_panel)
    normalize_topology_labels(topology, waveform_panel=waveform_panel)
    record_stage(
        "intro.topology",
        run_time=total_run_time,
        component_strokes=len(component_strokes),
        wire_strokes=len(wire_strokes),
        panel_strokes=len(panel_strokes),
    )
