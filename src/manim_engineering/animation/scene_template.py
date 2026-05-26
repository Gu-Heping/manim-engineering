"""Teaching-scene intro staging: stroke-first topology reveal without VGroup opacity."""

from __future__ import annotations

from manim import Animation, Create, DrawBorderThenFill, LaggedStart, VGroup

from manim_engineering.animation.focus import normalize_topology_labels
from manim_engineering.animation.intro_style import IntroStyle
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.trace import record_stage
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    apply_symbol_opacity,
    hide_labels,
    iter_symbol_strokes,
    partition_symbol_strokes,
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


def _lagged_border_fills(
    mobjects: tuple[object, ...],
    run_time: float,
    lag_ratio: float,
) -> Animation:
    if not mobjects:
        from manim import Wait

        return Wait(run_time=run_time)
    if len(mobjects) == 1:
        return DrawBorderThenFill(mobjects[0], run_time=run_time)
    return LaggedStart(
        *[DrawBorderThenFill(mob, run_time=run_time) for mob in mobjects],
        lag_ratio=lag_ratio,
    )


def _intro_anims_for_strokes(
    strokes: tuple[object, ...],
    *,
    line_run_time: float,
    intro_style: IntroStyle,
) -> Animation:
    line_strokes, filled_strokes = partition_symbol_strokes(strokes)
    parts: list[Animation] = []
    if line_strokes:
        parts.append(_lagged_creates(line_strokes, line_run_time, intro_style.create_lag_ratio))
    if filled_strokes:
        if intro_style.use_border_fill:
            parts.append(
                _lagged_border_fills(
                    filled_strokes,
                    intro_style.border_fill_run_time,
                    intro_style.create_lag_ratio,
                )
            )
        else:
            parts.append(
                _lagged_creates(filled_strokes, line_run_time, intro_style.create_lag_ratio)
            )
    if not parts:
        from manim import Wait

        return Wait(run_time=line_run_time)
    if len(parts) == 1:
        return parts[0]
    return LaggedStart(*parts, lag_ratio=intro_style.create_lag_ratio)


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
    intro_style: IntroStyle | None = None,
) -> None:
    """Reveal circuit bodies with stroke-first intro animations.

    ``Line`` bodies use ``Create``; ``Polygon``/``Dot`` use ``DrawBorderThenFill`` when
    :attr:`IntroStyle.use_border_fill` is enabled. Lag/stroke timing comes from
    ``intro_style`` (default :class:`IntroStyle`).

    Avoids ``FadeIn`` / ``set_opacity`` on heterogeneous ``topology.components`` groups,
    which activates default white fill on Manim ``Line`` symbols (resistor zig-zag bug).
    """
    scene = require_scene_methods(scene, require_play=True, require_add=True)
    style = intro_style or IntroStyle()

    component_strokes = iter_symbol_strokes(topology.components)
    wire_strokes = iter_symbol_strokes(topology.wires)
    panel_strokes = iter_symbol_strokes(waveform_panel)
    prepare_stroke_reveal(component_strokes)
    prepare_stroke_reveal(wire_strokes)
    prepare_stroke_reveal(panel_strokes)

    line_count = sum(
        len(partition_symbol_strokes(group)[0])
        for group in (component_strokes, wire_strokes, panel_strokes)
    )
    filled_count = sum(
        len(partition_symbol_strokes(group)[1])
        for group in (component_strokes, wire_strokes, panel_strokes)
    )

    hide_labels(topology.components)
    hide_labels(waveform_panel)
    scene.add(content)
    scene.play(
        LaggedStart(
            _intro_anims_for_strokes(
                component_strokes,
                line_run_time=components_run_time,
                intro_style=style,
            ),
            _intro_anims_for_strokes(
                wire_strokes,
                line_run_time=wires_run_time,
                intro_style=style,
            ),
            _intro_anims_for_strokes(
                panel_strokes,
                line_run_time=panel_run_time,
                intro_style=style,
            ),
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
        line_stroke_count=line_count,
        filled_stroke_count=filled_count,
        use_border_fill=style.use_border_fill,
    )
