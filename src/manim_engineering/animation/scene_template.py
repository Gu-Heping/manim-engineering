"""Teaching-scene intro staging: stroke-first topology reveal without VGroup opacity."""

from __future__ import annotations

from manim import Animation, Create, FadeIn, LaggedStart, VGroup

from manim_engineering.animation.focus import normalize_topology_labels
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
    """Reveal circuit bodies with ``Create`` on strokes; fade the timing panel separately.

    Avoids ``FadeIn`` / ``set_opacity`` on heterogeneous ``topology.components`` groups,
    which activates default white fill on Manim ``Line`` symbols (resistor zig-zag bug).
    """
    add = getattr(scene, "add", None)
    play = getattr(scene, "play", None)
    if add is None or play is None:
        msg = "scene must provide add() and play() like manim.Scene"
        raise TypeError(msg)

    component_strokes = iter_symbol_strokes(topology.components)
    wire_strokes = iter_symbol_strokes(topology.wires)
    prepare_stroke_reveal(component_strokes)
    prepare_stroke_reveal(wire_strokes)
    waveform_panel.set_opacity(0.0)

    hide_labels(topology.components)
    hide_labels(waveform_panel)
    add(content)
    play(
        LaggedStart(
            _lagged_creates(component_strokes, components_run_time, create_lag_ratio),
            _lagged_creates(wire_strokes, wires_run_time, create_lag_ratio),
            FadeIn(waveform_panel, run_time=panel_run_time),
            lag_ratio=lag_ratio,
        ),
        run_time=total_run_time,
    )
    apply_symbol_opacity(topology.components, 1.0)
    apply_symbol_opacity(topology.wires, 1.0)
    show_labels(topology.components)
    show_labels(waveform_panel)
    normalize_topology_labels(topology, waveform_panel=waveform_panel)
