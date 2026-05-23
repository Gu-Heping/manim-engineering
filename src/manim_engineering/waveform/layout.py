"""Waveform panel layout in world coordinates (no Manim)."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.semantic.enums import LogicLevel
from manim_engineering.waveform.trace import WaveformBundle, WaveformSample, WaveformTrace

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


def hud_text_y(
    frame_cy: float,
    frame_height: float,
    *,
    row: int = 0,
    margin: float = 0.55,
    row_gap: float = 0.50,
) -> float:
    """World Y for on-screen subtitles (row 0 = title band below top edge).

    ``row_gap`` is sized for the 3B1B-style HUD (title font_size 36, caption 26):
    the gap must exceed half the title height + half the caption height, which
    works out to ~0.40 world units at the standard pixel-aspect frame; 0.50
    leaves an extra 0.10 of optical breathing room.
    """
    top = frame_cy + frame_height / 2
    return top - margin - row * row_gap


def camera_frame_center(
    layout: LayoutResult,
    panel_spec: WaveformPanelSpec,
    *,
    trace_count: int,
) -> tuple[float, float]:
    """
    Camera center from layout geometry (not Manim mobject bounds).

    Waveform VMobject bounding boxes can extend far past ``panel_spec.width`` when
    ``time_scale`` is unset; using ``VGroup.get_center()`` mis-frames the shot.
    """
    scene = layout.scene_bbox
    panel_bottom = panel_spec.origin.y - panel_height(
        trace_count,
        panel_spec.trace_height,
        panel_spec.trace_gap,
    )
    cx = (scene.min_x + scene.max_x) * 0.5
    cy = (scene.max_y + panel_bottom) * 0.5
    return cx, cy


def time_scale_for_bundle(
    bundle: WaveformBundle,
    panel_width: float,
) -> float:
    """Scale trace times so the last sample aligns with ``panel_width``."""
    max_time = 1.0
    for trace in bundle.traces:
        if trace.samples:
            max_time = max(max_time, float(trace.samples[-1].time))
    return panel_width / max_time


def scene_frame_bounds(
    layout: LayoutResult,
    panel_spec: WaveformPanelSpec,
    *,
    trace_count: int,
    padding: float = 0.5,
    label_inset: float = 0.4,
    target_fill: float | None = None,
) -> tuple[float, float]:
    """Nominal Manim frame (width, height) covering circuit, wires, and waveform panel.

    Height spans from ``scene.max_y`` (top of routed content) down to the
    *bottom* of the waveform panel so the panel is never cropped. Earlier
    versions stopped at ``panel_spec.origin.y`` (panel top) which dropped the
    traces themselves out of frame.
    """
    scene = layout.scene_bbox
    content_w = max(scene.width, panel_spec.width) + label_inset
    panel_bottom = panel_spec.origin.y - panel_height(
        trace_count,
        panel_spec.trace_height,
        panel_spec.trace_gap,
    )
    content_h = scene.max_y - panel_bottom
    if target_fill is not None:
        if not 0.0 < target_fill <= 1.0:
            msg = f"target_fill must be in (0, 1], got {target_fill}"
            raise ValueError(msg)
        content_w /= target_fill
        content_h /= target_fill
    width = content_w + 2 * padding
    height = content_h + 2 * padding
    return width, max(height, 1.0)


def frame_size_for_pixel_aspect(
    width: float,
    height: float,
    *,
    pixel_width: float,
    pixel_height: float,
) -> tuple[float, float]:
    """
    Adjust Manim frame size so ``width / height`` equals ``pixel_width / pixel_height``.

    Without this, dots and text look squashed when exporting to 16:9 video.
    """
    if pixel_width <= 0 or pixel_height <= 0:
        msg = "pixel_width and pixel_height must be positive"
        raise ValueError(msg)
    target_aspect = pixel_width / pixel_height
    if width / height < target_aspect:
        return height * target_aspect, height
    return width, width / target_aspect


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
    *,
    max_beat: int | None = None,
    idle_only: bool = False,
) -> tuple[Point2D, ...]:
    """Orthogonal digital steps: hold level, then vertical edge at next sample.

    ``idle_only``: only the first sample (idle level) extended to panel width.
    ``max_beat``: include edges ``0..max_beat`` (needs ``max_beat + 2`` samples).
    ``max_beat is None``: full trace history.
    """
    if not trace.samples:
        return ()
    if idle_only:
        sample_slice = trace.samples[:1]
    elif max_beat is not None:
        end = min(max_beat + 2, len(trace.samples))
        sample_slice = trace.samples[: max(end, 1)]
    else:
        sample_slice = trace.samples

    points: list[Point2D] = []
    for index, sample in enumerate(sample_slice):
        pt = sample_to_point(sample, spec, trace_index)
        if index == 0:
            points.append(pt)
            continue
        prev = sample_slice[index - 1]
        corner = Point2D(pt.x, sample_to_point(prev, spec, trace_index).y)
        points.append(corner)
        points.append(pt)
    last = sample_slice[-1]
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


def transition_segment_for_beat(
    trace: WaveformTrace,
    beat: int,
    spec: WaveformPanelSpec,
    trace_index: int,
) -> tuple[Point2D, ...] | None:
    """
    Short polyline along the vertical edge at ``beat`` (for timing overlays).

    Returns hold point, corner, and edge endpoint — empty if beat is invalid.
    """
    history_edges = max(0, len(trace.samples) - 1)
    resolved_beat = beat
    if beat < 0:
        resolved_beat = history_edges + beat
    sample_index = resolved_beat + 1
    if resolved_beat < 0 or sample_index >= len(trace.samples):
        return None
    if sample_index < 1:
        return None

    prev_sample = trace.samples[sample_index - 1]
    edge_sample = trace.samples[sample_index]
    hold = sample_to_point(prev_sample, spec, trace_index)
    edge = sample_to_point(edge_sample, spec, trace_index)
    corner = Point2D(edge.x, hold.y)
    return (hold, corner, edge)
