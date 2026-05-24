"""Progressive waveform trace reveal synchronized with propagation beats."""

from __future__ import annotations

from manim import Line, VGroup

from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.waveform import (
    WaveformPanelRenderer,
    _point3,
    _trace_color,
)
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec, beat_for_time, step_polyline
from manim_engineering.waveform.trace import WaveformBundle, WaveformTrace

_SegmentKey = tuple[float, float, float, float]


class WaveformRevealTracker:
    """Update trace polylines in a rendered panel as beats advance."""

    def __init__(
        self,
        panel: VGroup,
        bundle: WaveformBundle,
        spec: WaveformPanelSpec,
        renderer: WaveformPanelRenderer | None = None,
    ) -> None:
        self._panel = panel
        self._bundle = bundle
        self._spec = spec
        self._renderer = renderer or WaveformPanelRenderer()
        self._axis_index = len(bundle.traces)
        self._revealed: dict[str, int] = {trace.signal_name: -1 for trace in bundle.traces}
        self._revealed_time: dict[str, float] = {trace.signal_name: -1.0 for trace in bundle.traces}
        self._segment_snapshots: dict[str, tuple[_SegmentKey, ...]] = {
            trace.signal_name: () for trace in bundle.traces
        }

    @property
    def panel(self) -> VGroup:
        return self._panel

    def reveal_for_beat(self, signal: Signal, wave_beat: int) -> None:
        """Extend the named trace through ``wave_beat`` (edge index)."""
        name = signal.name
        if name not in self._revealed:
            return
        self._revealed[name] = max(self._revealed[name], wave_beat)
        self._refresh_trace(name)

    def append_through_beat(self, signal: Signal, target_beat: int) -> tuple[object, ...]:
        """Reveal through ``target_beat``; return line mobjects to animate."""
        return self._sync_trace_to_time(signal.name, target_beat=target_beat)

    def append_through_time(self, reveal_time: float) -> tuple[object, ...]:
        """Reveal every trace up to shared semantic ``reveal_time``."""
        added: list[object] = []
        for trace in self._bundle.traces:
            added.extend(
                self._sync_trace_to_time(trace.signal_name, hold_through_time=reveal_time)
            )
        return tuple(added)

    def _sync_trace_to_time(
        self,
        name: str,
        *,
        target_beat: int | None = None,
        hold_through_time: float | None = None,
    ) -> tuple[object, ...]:
        if name not in self._revealed:
            return ()

        trace_index = next(
            i for i, trace in enumerate(self._bundle.traces) if trace.signal_name == name
        )
        trace = self._bundle.traces[trace_index]
        if target_beat is None:
            if hold_through_time is None:
                return ()
            target_beat = beat_for_time(trace, hold_through_time)

        current_beat = self._revealed[name]
        current_time = self._revealed_time[name]
        if target_beat <= current_beat and (
            hold_through_time is None or hold_through_time <= current_time
        ):
            return ()

        trace_group = self._panel.submobjects[trace_index]
        label = trace_group.submobjects[-1]
        previous_keys = self._segment_snapshots[name]

        new_segments = self._line_segments(
            trace,
            trace_index,
            target_beat,
            hold_through_time=hold_through_time,
        )
        new_keys = tuple(_segment_key(line) for line in new_segments)

        for line in self._line_children(trace_group):
            trace_group.remove(line)

        to_animate: list[object] = []
        trace_group.remove(label)
        for index, line in enumerate(new_segments):
            changed = index >= len(previous_keys) or new_keys[index] != previous_keys[index]
            if changed:
                line.set_stroke(
                    color=_trace_color(trace),
                    width=0.0,
                    opacity=1.0,
                )
                to_animate.append(line)
            trace_group.add(line)
        trace_group.add(label)

        self._revealed[name] = target_beat
        if hold_through_time is not None:
            self._revealed_time[name] = max(self._revealed_time[name], hold_through_time)
        self._segment_snapshots[name] = new_keys

        return tuple(to_animate)

    def finalize_reveal(self, signal: Signal) -> None:
        """Extend the trace hold line to the panel edge after progressive reveal."""
        name = signal.name
        if name not in self._revealed or self._revealed[name] < 0:
            return
        self._refresh_trace(name, extend_to_panel=True)

    def reveal_all(self) -> None:
        """Show full history on every trace (end of sequence)."""
        for trace in self._bundle.traces:
            edges = max(0, len(trace.samples) - 2)
            self._revealed[trace.signal_name] = edges
            self._refresh_trace(trace.signal_name, extend_to_panel=True)
            self._segment_snapshots[trace.signal_name] = ()

    def _line_children(self, trace_group: VGroup) -> list[object]:
        return list(trace_group.submobjects[:-1])

    def _line_segments(
        self,
        trace: WaveformTrace,
        trace_index: int,
        max_beat: int,
        *,
        extend_to_panel: bool = False,
        hold_through_time: float | None = None,
    ) -> list[Line]:
        points = step_polyline(
            trace,
            self._spec,
            trace_index,
            max_beat=max_beat,
            extend_to_panel=extend_to_panel,
            hold_through_time=hold_through_time,
        )
        color = _trace_color(trace)
        segments: list[Line] = []
        for start, end in zip(points, points[1:], strict=False):
            if start.x == end.x and start.y == end.y:
                continue
            segments.append(
                Line(
                    _point3(start),
                    _point3(end),
                    stroke_color=color,
                    stroke_width=theme.WAVEFORM_STROKE_WIDTH,
                )
            )
        return segments

    def _refresh_trace(self, signal_name: str, *, extend_to_panel: bool | None = None) -> None:
        trace_index = next(
            i for i, t in enumerate(self._bundle.traces) if t.signal_name == signal_name
        )
        trace = self._bundle.traces[trace_index]
        max_beat = self._revealed[signal_name]
        if extend_to_panel is None:
            full_edges = max(0, len(trace.samples) - 2)
            extend_to_panel = max_beat >= full_edges
        new_group = self._renderer.render_trace(
            trace,
            self._spec,
            trace_index,
            max_beat=max_beat if max_beat >= 0 else None,
            idle_only=max_beat < 0,
            extend_to_panel=extend_to_panel,
        )
        self._panel.submobjects[trace_index] = new_group


def _segment_key(line: Line) -> _SegmentKey:
    start = line.get_start()
    end = line.get_end()
    return (
        round(float(start[0]), 6),
        round(float(start[1]), 6),
        round(float(end[0]), 6),
        round(float(end[1]), 6),
    )
