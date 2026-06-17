"""Teaching-scene intro staging: stroke-first topology reveal without VGroup opacity."""

from __future__ import annotations

from manim import Animation, Create, DrawBorderThenFill, LaggedStart, Mobject, VGroup

from manim_engineering.animation.intro_plan import (
    ComponentIntroOrder,
    IntroPlan,
    build_intro_plan,
)
from manim_engineering.animation.intro_style import IntroStyle, intro_run_time_budget
from manim_engineering.animation.scene_protocol import require_scene_methods
from manim_engineering.animation.stage_record import record_plain_stage
from manim_engineering.animation.trace import record_stage
from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import (
    apply_symbol_opacity,
    hide_labels,
    iter_symbol_strokes,
    normalize_stroke_only_geometry,
    partition_symbol_strokes,
    prepare_stroke_reveal,
    refresh_label_strokes,
    restore_stroke_reveal,
    restore_waveform_strokes,
    show_labels,
)


def _stroke_intro_animation(mob: object, intro_style: IntroStyle) -> Animation:
    if mob.__class__.__name__ == "Line":
        return Create(mob)
    if intro_style.use_border_fill:
        return DrawBorderThenFill(mob)
    return Create(mob)


def _intro_anims_for_strokes(
    strokes: tuple[object, ...],
    *,
    intro_style: IntroStyle,
) -> Animation:
    line_strokes, filled_strokes = partition_symbol_strokes(strokes)
    ordered = (*line_strokes, *filled_strokes)
    if not ordered:
        from manim import Wait

        return Wait()
    if len(ordered) == 1:
        return _stroke_intro_animation(ordered[0], intro_style)
    return LaggedStart(
        *[_stroke_intro_animation(mob, intro_style) for mob in ordered],
        lag_ratio=intro_style.create_lag_ratio,
    )


def _stroke_anim_count(strokes: tuple[object, ...]) -> int:
    if not strokes:
        return 0
    line_strokes, filled_strokes = partition_symbol_strokes(strokes)
    return len(line_strokes) + len(filled_strokes)


def _stage_run_time(
    strokes: tuple[object, ...],
    intro_style: IntroStyle,
    *,
    override: float | None = None,
) -> float:
    if not strokes:
        return 0.0
    if override is not None and override > 0.0:
        return override
    return intro_run_time_budget(_stroke_anim_count(strokes), intro_style)


def _play_intro_stage(
    scene: object,
    strokes: tuple[object, ...],
    intro_style: IntroStyle,
    *,
    run_time: float,
) -> float:
    if not strokes or run_time <= 0.0:
        return 0.0
    scene = require_scene_methods(scene, require_play=True)
    scene.play(_intro_anims_for_strokes(strokes, intro_style=intro_style), run_time=run_time)
    restore_stroke_reveal(strokes)
    return run_time


def _stage_strokes_by_prefix(plan: IntroPlan, prefix: str) -> tuple[object, ...]:
    strokes: list[object] = []
    for stage in plan.stages:
        if stage.name == prefix or stage.name.startswith(f"{prefix}:"):
            strokes.extend(stage.strokes)
    return tuple(strokes)


def _iter_trace_line_strokes(waveform_panel: VGroup) -> tuple[Mobject, ...]:
    """Trace polyline segments (excludes axis chrome and per-trace labels)."""
    if len(waveform_panel.submobjects) < 2:
        return ()
    strokes: list[Mobject] = []
    for trace_group in waveform_panel.submobjects[:-1]:
        if not isinstance(trace_group, VGroup):
            continue
        for mob in trace_group.submobjects:
            if mob.__class__.__name__ == "Line" and len(mob.points) > 0:
                strokes.append(mob)
    return tuple(strokes)


def _iter_panel_chrome_strokes(waveform_panel: VGroup) -> tuple[Mobject, ...]:
    """Panel axis/chrome only (no trace polylines)."""
    if not waveform_panel.submobjects:
        return ()
    axis = waveform_panel.submobjects[-1]
    if axis.__class__.__name__ == "Line" and len(axis.points) > 0:
        return (axis,)
    return iter_symbol_strokes(axis)


def _iter_trace_line_strokes_for_traces(
    waveform_panel: VGroup,
    trace_indices: frozenset[int],
) -> tuple[Mobject, ...]:
    """Trace polyline segments for selected trace row indices."""
    strokes: list[Mobject] = []
    for trace_index in sorted(trace_indices):
        if trace_index < 0 or trace_index >= len(waveform_panel.submobjects):
            continue
        trace_group = waveform_panel.submobjects[trace_index]
        if not isinstance(trace_group, VGroup):
            continue
        for mob in trace_group.submobjects:
            if mob.__class__.__name__ == "Line" and len(mob.points) > 0:
                strokes.append(mob)
    return tuple(strokes)


def play_waveform_idle_baseline(
    scene: object,
    waveform_panel: VGroup,
    *,
    run_time: float = 0.4,
    lag_ratio: float = 0.15,
    baseline_traces: frozenset[str] | None = None,
    bundle: object | None = None,
) -> None:
    """Reveal idle trace stubs after topology intro (one ``Create`` per selected trace).

    When ``baseline_traces`` is set, only those signal names are animated; other
    traces stay hidden until their first propagation beat.
    """
    scene = require_scene_methods(scene, require_play=True)
    if baseline_traces is not None and bundle is not None:
        from manim_engineering.waveform.trace import WaveformBundle

        if isinstance(bundle, WaveformBundle):
            indices = frozenset(
                index
                for index, trace in enumerate(bundle.traces)
                if trace.signal_name in baseline_traces
            )
            trace_lines = _iter_trace_line_strokes_for_traces(waveform_panel, indices)
        else:
            trace_lines = _iter_trace_line_strokes(waveform_panel)
    else:
        trace_lines = _iter_trace_line_strokes(waveform_panel)
    if not trace_lines:
        return
    if len(trace_lines) == 1:
        scene.play(Create(trace_lines[0]), run_time=run_time)
    else:
        scene.play(
            LaggedStart(*[Create(line) for line in trace_lines], lag_ratio=lag_ratio),
            run_time=run_time,
        )
    restore_waveform_strokes(trace_lines)
    record_plain_stage(
        "intro.waveform_baseline",
        run_time=run_time,
        trace_count=len(trace_lines),
        record=record_stage,
    )


def play_topology_intro(
    scene: object,
    topology: TopologyProjection,
    waveform_panel: VGroup,
    content: VGroup,
    *,
    components_run_time: float | None = None,
    wires_run_time: float | None = None,
    panel_run_time: float | None = None,
    lag_ratio: float = 0.15,
    total_run_time: float | None = None,
    include_panel_traces: bool = False,
    component_order: ComponentIntroOrder = "grouped",
    intro_style: IntroStyle | None = None,
    intro_plan: IntroPlan | None = None,
    reveal_component_labels: bool = True,
    reveal_net_labels: bool = True,
    reveal_panel_labels: bool = True,
) -> None:
    """Reveal circuit bodies with stroke-first intro animations.

    ``Line`` bodies use ``Create``; ``Polygon``/``Dot`` use ``DrawBorderThenFill`` when
    :attr:`IntroStyle.use_border_fill` is enabled. Stages play sequentially (components,
    wires, panel chrome) with per-stage run-time budgets from stroke count.

    When ``include_panel_traces`` is ``False`` (default for waveform scenes), trace
    polylines stay hidden until :func:`play_waveform_idle_baseline`.
    """
    scene = require_scene_methods(scene, require_play=True, require_add=True)
    style = intro_style or IntroStyle()
    _ = lag_ratio
    plan = intro_plan or build_intro_plan(
        topology,
        waveform_panel,
        components_run_time=components_run_time,
        wires_run_time=wires_run_time,
        panel_run_time=panel_run_time,
        include_panel_traces=include_panel_traces,
        component_order=component_order,
    )

    component_strokes = _stage_strokes_by_prefix(plan, "component") or _stage_strokes_by_prefix(
        plan, "components"
    )
    wire_strokes = _stage_strokes_by_prefix(plan, "wires")
    panel_strokes = _stage_strokes_by_prefix(plan, "panel")
    if plan.include_panel_traces:
        panel_strokes = iter_symbol_strokes(waveform_panel)
    else:
        prepare_stroke_reveal(_iter_trace_line_strokes(waveform_panel))

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
    apply_symbol_opacity(topology.components, 0.0)
    apply_symbol_opacity(topology.wires, 0.0)
    apply_symbol_opacity(waveform_panel, 0.0)
    scene.add(content)

    stage_specs = [
        (stage.strokes, stage.run_time_override)
        for stage in plan.stages
        if stage.run_time_override is None or stage.run_time_override > 0.0
    ]

    stage_budgets = [
        _stage_run_time(strokes, style, override=override)
        for strokes, override in stage_specs
        if strokes
    ]
    if total_run_time is not None and stage_budgets:
        scale = total_run_time / sum(stage_budgets)
        stage_budgets = [budget * scale for budget in stage_budgets]

    played_run_time = 0.0
    budget_index = 0
    for strokes, _override in stage_specs:
        if not strokes:
            continue
        run_time = stage_budgets[budget_index]
        budget_index += 1
        played_run_time += _play_intro_stage(scene, strokes, style, run_time=run_time)

    apply_symbol_opacity(topology.components, 1.0)
    apply_symbol_opacity(topology.wires, 1.0)
    if include_panel_traces:
        apply_symbol_opacity(waveform_panel, 1.0)
    if reveal_component_labels:
        show_labels(topology.components, roles=("component_label",))
    if reveal_net_labels:
        show_labels(topology.components, roles=("net_label",))
    if reveal_panel_labels:
        show_labels(waveform_panel)
    normalize_stroke_only_geometry(topology.components)
    normalize_stroke_only_geometry(topology.wires)
    if reveal_component_labels or reveal_net_labels:
        reveal_roles: list[str] = []
        if reveal_component_labels:
            reveal_roles.append("component_label")
        if reveal_net_labels:
            reveal_roles.append("net_label")
        refresh_label_strokes(topology.components, mode="full", roles=tuple(reveal_roles))
    if reveal_panel_labels:
        normalize_stroke_only_geometry(waveform_panel)
        refresh_label_strokes(waveform_panel, mode="full")
    record_plain_stage(
        "intro.topology",
        run_time=played_run_time,
        component_strokes=len(component_strokes),
        wire_strokes=len(wire_strokes),
        panel_strokes=len(panel_strokes),
        line_stroke_count=line_count,
        filled_stroke_count=filled_count,
        use_border_fill=style.use_border_fill,
        include_panel_traces=include_panel_traces,
        record=record_stage,
    )
