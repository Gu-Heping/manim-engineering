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
    label_inset: float = 0.55,
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


def _sample_slice_for_polyline(
    trace: WaveformTrace,
    *,
    idle_only: bool,
    max_beat: int | None,
    hold_through_time: float | None,
) -> tuple[WaveformSample, ...]:
    if not trace.samples:
        return ()
    if idle_only:
        return trace.samples[:1]
    if hold_through_time is not None:
        return _samples_through_time(trace.samples, hold_through_time)
    if max_beat is not None:
        end = min(max_beat + 2, len(trace.samples))
        return trace.samples[: max(end, 1)]
    return trace.samples


def _samples_through_time(
    samples: tuple[WaveformSample, ...],
    hold_through_time: float,
) -> tuple[WaveformSample, ...]:
    """Include every sample at or before ``hold_through_time``, interpolating the tail."""
    if not samples:
        return ()
    included: list[WaveformSample] = []
    for sample in samples:
        if sample.time <= hold_through_time + 1e-9:
            included.append(sample)
        else:
            break
    if not included:
        included.append(_interpolate_sample_at_time(samples, hold_through_time))
    last = included[-1]
    if last.time < hold_through_time - 1e-9:
        included.append(_interpolate_sample_at_time(samples, hold_through_time))
    return tuple(included)


def _interpolate_sample_at_time(
    samples: tuple[WaveformSample, ...],
    target_time: float,
) -> WaveformSample:
    if target_time <= samples[0].time:
        return WaveformSample(time=target_time, level=samples[0].level)
    for index in range(1, len(samples)):
        current = samples[index]
        if current.time >= target_time:
            previous = samples[index - 1]
            if current.time == previous.time:
                return WaveformSample(time=target_time, level=current.level)
            fraction = (target_time - previous.time) / (current.time - previous.time)
            prev_level = previous.level
            curr_level = current.level
            if isinstance(prev_level, float) and isinstance(curr_level, float):
                level: LogicLevel | float = prev_level + fraction * (curr_level - prev_level)
            else:
                level = prev_level
            return WaveformSample(time=target_time, level=level)
    last = samples[-1]
    return WaveformSample(time=target_time, level=last.level)


def smooth_polyline(
    trace: WaveformTrace,
    spec: WaveformPanelSpec,
    trace_index: int,
    *,
    max_beat: int | None = None,
    idle_only: bool = False,
    extend_to_panel: bool | None = None,
    hold_through_time: float | None = None,
) -> tuple[Point2D, ...]:
    """Continuous trace polyline: connect samples directly (linear hold between points)."""
    sample_slice = _sample_slice_for_polyline(
        trace,
        idle_only=idle_only,
        max_beat=max_beat,
        hold_through_time=hold_through_time,
    )
    if not sample_slice:
        return ()

    if extend_to_panel is None:
        extend_to_panel = idle_only or (max_beat is None and hold_through_time is None)

    points: list[Point2D] = []
    for sample in sample_slice:
        _append_point_if_distinct(points, sample_to_point(sample, spec, trace_index))

    last_pt = sample_to_point(sample_slice[-1], spec, trace_index)
    if hold_through_time is not None:
        hold_x = spec.origin.x + hold_through_time * spec.time_scale
        _append_point_if_distinct(points, Point2D(hold_x, last_pt.y))
        if extend_to_panel:
            end_x = spec.origin.x + spec.width
            if points and points[-1].x < end_x - 1e-9:
                _append_point_if_distinct(points, Point2D(end_x, points[-1].y))
    elif extend_to_panel:
        end_x = spec.origin.x + spec.width
        _append_point_if_distinct(points, Point2D(end_x, last_pt.y))
    return tuple(points)


def polyline_for_trace(
    trace: WaveformTrace,
    spec: WaveformPanelSpec,
    trace_index: int,
    **kwargs: object,
) -> tuple[Point2D, ...]:
    """Dispatch to ``step_polyline`` or ``smooth_polyline`` based on ``trace.is_discrete``."""
    if trace.is_discrete:
        return step_polyline(trace, spec, trace_index, **kwargs)  # type: ignore[arg-type]
    return smooth_polyline(trace, spec, trace_index, **kwargs)  # type: ignore[arg-type]


def step_polyline(
    trace: WaveformTrace,
    spec: WaveformPanelSpec,
    trace_index: int,
    *,
    max_beat: int | None = None,
    idle_only: bool = False,
    extend_to_panel: bool | None = None,
    hold_through_time: float | None = None,
) -> tuple[Point2D, ...]:
    """Orthogonal digital steps: hold level, then vertical edge at next sample.

    ``idle_only``: only the first sample (idle level) extended to panel width.
    ``max_beat``: include edges ``0..max_beat`` (needs ``max_beat + 2`` samples).
    ``max_beat is None``: full trace history.
    ``extend_to_panel``: when ``True``, append a horizontal hold to the panel's
        right edge; when ``False``, stop at the last revealed sample (progressive
        reveal). Defaults to ``idle_only or max_beat is None``.
    """
    sample_slice = _sample_slice_for_polyline(
        trace,
        idle_only=idle_only,
        max_beat=max_beat,
        hold_through_time=hold_through_time,
    )
    if not sample_slice:
        return ()

    if extend_to_panel is None:
        extend_to_panel = idle_only or (max_beat is None and hold_through_time is None)

    points: list[Point2D] = []
    for index, sample in enumerate(sample_slice):
        pt = sample_to_point(sample, spec, trace_index)
        if index == 0:
            _append_point_if_distinct(points, pt)
            continue
        prev = sample_slice[index - 1]
        corner = Point2D(pt.x, sample_to_point(prev, spec, trace_index).y)
        _append_point_if_distinct(points, corner)
        _append_point_if_distinct(points, pt)
    last = sample_slice[-1]
    last_y = sample_to_point(last, spec, trace_index).y
    if hold_through_time is not None:
        hold_x = spec.origin.x + hold_through_time * spec.time_scale
        _append_point_if_distinct(points, Point2D(hold_x, last_y))
    elif extend_to_panel:
        end_x = spec.origin.x + spec.width
        _append_point_if_distinct(points, Point2D(end_x, last_y))
    return tuple(points)


def _append_point_if_distinct(points: list[Point2D], pt: Point2D) -> None:
    if points and points[-1].x == pt.x and points[-1].y == pt.y:
        return
    points.append(pt)


def beat_for_time(trace: WaveformTrace, reveal_time: float) -> int:
    """Edge index that includes every sample at or before ``reveal_time``."""
    eligible = [
        index for index, sample in enumerate(trace.samples) if sample.time <= reveal_time + 1e-9
    ]
    if not eligible:
        return -1
    return max(-1, max(eligible) - 1)


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
