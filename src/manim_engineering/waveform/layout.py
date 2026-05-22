"""Waveform panel layout in world coordinates (no Manim)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.waveform.trace import WaveformSample, WaveformTrace

MIN_WAVEFORM_GAP = 0.35


@dataclass(frozen=True)
class WaveformPanelSpec:
    """Panel region below a placed circuit for aligned timing traces."""

    origin: Point2D
    width: float
    trace_height: float
    trace_gap: float
    time_scale: float = 1.0

    def trace_origin_y(self, trace_index: int) -> float:
        """Bottom Y for trace row ``trace_index`` (0 = topmost trace)."""
        row = self.trace_height + self.trace_gap
        return self.origin.y - trace_index * row

    def panel_height(self, trace_count: int) -> float:
        if trace_count <= 0:
            return 0.0
        return trace_count * self.trace_height + (trace_count - 1) * self.trace_gap


def panel_below_layout(
    layout: LayoutResult,
    *,
    trace_count: int,
    trace_height: float = 0.25,
    trace_gap: float = 0.12,
    margin: float = MIN_WAVEFORM_GAP,
    width: float | None = None,
) -> WaveformPanelSpec:
    """Place waveform panel under the circuit scene bounding box (components + wires)."""
    bounds = layout.scene_bbox
    panel_width = width if width is not None else max(bounds.width, 1.5)
    below = panel_height(trace_count, trace_height, trace_gap)
    origin_y = bounds.min_y - margin - below
    return WaveformPanelSpec(
        origin=Point2D(bounds.min_x, origin_y),
        width=panel_width,
        trace_height=trace_height,
        trace_gap=trace_gap,
        time_scale=1.0,
    )


def scene_frame_bounds(
    layout: LayoutResult,
    panel_spec: WaveformPanelSpec,
    *,
    trace_count: int,
    padding: float = 0.5,
    label_inset: float = 0.4,
) -> tuple[float, float]:
    """Nominal Manim frame (width, height) covering circuit, wires, and waveform panel."""
    scene = layout.scene_bbox
    width = max(scene.width, panel_spec.width) + label_inset + 2 * padding
    height = (scene.max_y - panel_spec.origin.y) + 2 * padding
    return width, max(height, 1.0)


def panel_height(trace_count: int, trace_height: float, trace_gap: float) -> float:
    if trace_count <= 0:
        return 0.0
    return trace_count * trace_height + max(0, trace_count - 1) * trace_gap


def _digital_y(level: LogicLevel | float, trace_bottom: float, trace_height: float) -> float:
    if isinstance(level, LogicLevel):
        if level == LogicLevel.HIGH:
            return trace_bottom + 0.85 * trace_height
        return trace_bottom + 0.15 * trace_height
    mid = 0.5 * trace_height
    return trace_bottom + mid + float(level) * 0.35 * trace_height


def sample_to_point(
    sample: WaveformSample,
    spec: WaveformPanelSpec,
    trace_index: int,
) -> Point2D:
    """Map a semantic sample to panel world coordinates."""
    trace_bottom = spec.trace_origin_y(trace_index)
    x = spec.origin.x + sample.time * spec.time_scale
    y = _digital_y(sample.level, trace_bottom, spec.trace_height)
    return Point2D(x, y)


def step_polyline(
    trace: WaveformTrace,
    spec: WaveformPanelSpec,
    trace_index: int,
) -> tuple[Point2D, ...]:
    """Orthogonal digital steps: hold level, then vertical edge at next sample."""
    if not trace.samples:
        return ()
    points: list[Point2D] = []
    for index, sample in enumerate(trace.samples):
        pt = sample_to_point(sample, spec, trace_index)
        if index == 0:
            points.append(pt)
            continue
        prev = trace.samples[index - 1]
        corner = Point2D(pt.x, sample_to_point(prev, spec, trace_index).y)
        points.append(corner)
        points.append(pt)
    last = trace.samples[-1]
    end_x = spec.origin.x + spec.width
    end_pt = Point2D(end_x, sample_to_point(last, spec, trace_index).y)
    points.append(end_pt)
    return tuple(points)


def transition_point_for_beat(
    trace: WaveformTrace,
    beat: int,
    spec: WaveformPanelSpec,
    trace_index: int,
) -> Point2D | None:
    """World point at propagation beat (0 = first edge after initial sample)."""
    history_edges = max(0, len(trace.samples) - 1)
    if beat < 0:
        beat = history_edges + beat
    sample_index = beat + 1
    if beat < 0 or sample_index >= len(trace.samples):
        return None
    return sample_to_point(trace.samples[sample_index], spec, trace_index)
