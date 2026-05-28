"""Minimal renderer: timing traces (digital steps and analog curves) aligned with layout."""

from __future__ import annotations

from dataclasses import replace

from manim import Line, VGroup

from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.labels import label_text
from manim_engineering.waveform.layout import (
    MIN_WAVEFORM_GAP,
    WaveformPanelSpec,
    panel_below_layout,
    polyline_for_trace,
    time_scale_for_bundle,
)
from manim_engineering.waveform.trace import WaveformBundle, WaveformTrace


def point3(p: Point2D) -> list[float]:
    return [p.x, p.y, 0.0]


def trace_color(trace: WaveformTrace) -> object:
    return theme.color_for_signal_type(trace.signal_type)


_point3 = point3
_trace_color = trace_color


class WaveformPanelRenderer:
    """Draw waveform traces in a panel below the circuit (step or smooth polylines)."""

    def panel_spec_for_layout(
        self,
        layout: LayoutResult,
        bundle: WaveformBundle,
        *,
        trace_height: float = 0.25,
        trace_gap: float = 0.12,
        margin: float = MIN_WAVEFORM_GAP,
    ) -> WaveformPanelSpec:
        spec = panel_below_layout(
            layout,
            trace_count=len(bundle.traces),
            trace_height=trace_height,
            trace_gap=trace_gap,
            margin=margin,
        )
        return replace(
            spec,
            time_scale=time_scale_for_bundle(bundle, spec.width),
        )

    def render_trace(
        self,
        trace: WaveformTrace,
        spec: WaveformPanelSpec,
        trace_index: int,
        *,
        max_beat: int | None = None,
        idle_only: bool = False,
        extend_to_panel: bool | None = None,
        idle_extend_to_panel: bool = False,
    ) -> VGroup:
        group = VGroup()
        resolved_extend = extend_to_panel
        if idle_only and extend_to_panel is None:
            resolved_extend = idle_extend_to_panel
        points = polyline_for_trace(
            trace,
            spec,
            trace_index,
            max_beat=max_beat,
            idle_only=idle_only,
            extend_to_panel=resolved_extend,
        )
        color = _trace_color(trace)
        for start, end in zip(points, points[1:], strict=False):
            group.add(
                Line(
                    _point3(start),
                    _point3(end),
                    stroke_color=color,
                    stroke_width=theme.WAVEFORM_STROKE_WIDTH,
                )
            )
        label = label_text(
            trace.signal_name,
            font_size=theme.WAVEFORM_LABEL_FONT_SIZE,
            color=color,
        )
        label.move_to(
            [
                spec.origin.x - 0.35,
                spec.trace_origin_y(trace_index) + spec.trace_height * 0.5,
                0.0,
            ]
        )
        group.add(label)
        return group

    def render_bundle(
        self,
        bundle: WaveformBundle,
        spec: WaveformPanelSpec,
        *,
        idle_only: bool = False,
    ) -> VGroup:
        panel = VGroup()
        for index, trace in enumerate(bundle.traces):
            panel.add(
                self.render_trace(
                    trace,
                    spec,
                    index,
                    idle_only=idle_only,
                )
            )
        axis = Line(
            _point3(spec.origin),
            _point3(Point2D(spec.origin.x + spec.width, spec.origin.y)),
            stroke_color=theme.GROUND_COLOR,
            stroke_width=theme.HELPER_STROKE_WIDTH,
        )
        panel.add(axis)
        return panel

    def render_with_layout(
        self,
        bundle: WaveformBundle,
        layout: LayoutResult,
        *,
        idle_only: bool = False,
    ) -> tuple[VGroup, WaveformPanelSpec]:
        spec = self.panel_spec_for_layout(layout, bundle)
        return self.render_bundle(bundle, spec, idle_only=idle_only), spec
