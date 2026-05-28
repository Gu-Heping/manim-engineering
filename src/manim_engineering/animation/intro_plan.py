"""Intro planning for teaching-scene topology reveal."""

from __future__ import annotations

from dataclasses import dataclass

from manim import Mobject, VGroup

from manim_engineering.renderers.minimal.immutable import TopologyProjection
from manim_engineering.renderers.minimal.labels import iter_symbol_strokes


@dataclass(frozen=True)
class IntroStagePlan:
    """One intro reveal stage with a stable semantic name and stroke group."""

    name: str
    strokes: tuple[Mobject, ...]
    run_time_override: float | None = None


@dataclass(frozen=True)
class IntroPlan:
    """Ordered reveal stages for a topology intro."""

    stages: tuple[IntroStagePlan, ...]
    include_panel_traces: bool = False


def _iter_trace_line_strokes(waveform_panel: VGroup) -> tuple[Mobject, ...]:
    if len(waveform_panel.submobjects) < 2:
        return ()
    strokes: list[Mobject] = []
    for trace_group in waveform_panel.submobjects[:-1]:
        if not isinstance(trace_group, VGroup):
            continue
        for mob in trace_group.submobjects[:-1]:
            if mob.__class__.__name__ == "Line" and len(mob.points) > 0:
                strokes.append(mob)
    return tuple(strokes)


def _iter_panel_chrome_strokes(waveform_panel: VGroup) -> tuple[Mobject, ...]:
    if not waveform_panel.submobjects:
        return ()
    axis = waveform_panel.submobjects[-1]
    if axis.__class__.__name__ == "Line" and len(axis.points) > 0:
        return (axis,)
    return iter_symbol_strokes(axis)


def build_intro_plan(
    topology: TopologyProjection,
    waveform_panel: VGroup,
    *,
    components_run_time: float | None = None,
    wires_run_time: float | None = None,
    panel_run_time: float | None = None,
    include_panel_traces: bool = False,
) -> IntroPlan:
    """Build the default stable intro order for teaching scenes."""

    panel_strokes = (
        iter_symbol_strokes(waveform_panel)
        if include_panel_traces
        else _iter_panel_chrome_strokes(waveform_panel)
    )
    stages = (
        IntroStagePlan(
            name="components",
            strokes=iter_symbol_strokes(topology.components),
            run_time_override=components_run_time,
        ),
        IntroStagePlan(
            name="wires",
            strokes=iter_symbol_strokes(topology.wires),
            run_time_override=wires_run_time,
        ),
        IntroStagePlan(
            name="panel",
            strokes=panel_strokes,
            run_time_override=panel_run_time,
        ),
    )
    return IntroPlan(
        stages=tuple(stage for stage in stages if stage.strokes),
        include_panel_traces=include_panel_traces,
    )
