"""Progressive waveform trace reveal synchronized with propagation beats."""

from __future__ import annotations

from dataclasses import dataclass

from manim import Line, VGroup

from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.labels import (
    prepare_stroke_reveal,
    restore_waveform_strokes,
)
from manim_engineering.renderers.minimal.waveform import (
    WaveformPanelRenderer,
    point3,
    trace_color,
)
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec, beat_for_time, polyline_for_trace
from manim_engineering.waveform.trace import WaveformBundle, WaveformTrace

_SegmentKey = tuple[float, float, float, float]


@dataclass(frozen=True)
class SegmentRevealPlan:
    """Stable-append reveal plan: prefix lines stay mounted; new segments mount at beat time."""

    trace_group: VGroup
    added: tuple[Line, ...] = ()
    removed: tuple[Line, ...] = ()


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

    def sync_idle_baselines(self) -> None:
        """Record idle baseline geometry after :func:`play_waveform_idle_baseline`."""
        for trace_index, trace in enumerate(self._bundle.traces):
            name = trace.signal_name
            trace_group = self._trace_group_for(trace_index)
            lines = self._line_children(trace_group)
            self._segment_snapshots[name] = tuple(_segment_key(line) for line in lines)
            self._revealed[name] = -1
            self._revealed_time[name] = 0.0

    def reveal_for_beat(self, signal: Signal, wave_beat: int) -> SegmentRevealPlan:
        """Reveal through ``wave_beat`` and mount segments (stable-append; no full trace swap)."""
        plan = self.append_through_beat(signal, wave_beat)
        mount_reveal_plan(plan)
        return plan

    def append_through_beat(self, signal: Signal, target_beat: int) -> SegmentRevealPlan:
        """Reveal through ``target_beat``; return segments to mount and animate with ``Create``."""
        return self._sync_trace_to_time(signal.name, target_beat=target_beat)

    def append_through_time(self, reveal_time: float) -> tuple[SegmentRevealPlan, ...]:
        """Reveal every trace up to shared semantic ``reveal_time``."""
        plans: list[SegmentRevealPlan] = []
        for trace in self._bundle.traces:
            plan = self._sync_trace_to_time(trace.signal_name, hold_through_time=reveal_time)
            if plan.added or plan.removed:
                plans.append(plan)
        return tuple(plans)

    def append_through_time_for(
        self,
        signal_name: str,
        reveal_time: float,
    ) -> SegmentRevealPlan:
        """Reveal one named trace up to ``reveal_time`` (mixed digital/analog scenes)."""
        return self._sync_trace_to_time(signal_name, hold_through_time=reveal_time)

    def revealed_time_for(self, signal_name: str) -> float:
        """Last semantic time revealed for ``signal_name`` (0.0 when still idle)."""
        return max(0.0, self._revealed_time.get(signal_name, -1.0))

    def _trace_index_for(self, name: str) -> int:
        for index, trace in enumerate(self._bundle.traces):
            if trace.signal_name == name:
                return index
        known = [trace.signal_name for trace in self._bundle.traces]
        msg = f"unknown waveform trace {name!r}; panel traces={known}"
        raise ValueError(msg)

    def _trace_group_for(self, trace_index: int) -> VGroup:
        if trace_index < 0 or trace_index >= len(self._panel.submobjects):
            msg = (
                "waveform panel structure mismatch: "
                f"trace_index={trace_index}, panel_groups={len(self._panel.submobjects)}, "
                f"bundle_traces={len(self._bundle.traces)}"
            )
            raise ValueError(msg)
        group = self._panel.submobjects[trace_index]
        if not isinstance(group, VGroup):
            msg = (
                "waveform panel structure mismatch: "
                f"trace_index={trace_index} expected VGroup, got {type(group).__name__}"
            )
            raise ValueError(msg)
        return group

    def _sync_trace_to_time(
        self,
        name: str,
        *,
        target_beat: int | None = None,
        hold_through_time: float | None = None,
        extend_to_panel: bool = False,
    ) -> SegmentRevealPlan:
        empty = SegmentRevealPlan(trace_group=VGroup())
        if name not in self._revealed:
            return empty

        trace_index = self._trace_index_for(name)
        trace = self._bundle.traces[trace_index]
        if target_beat is None:
            if hold_through_time is None:
                return empty
            target_beat = beat_for_time(trace, hold_through_time)

        current_beat = self._revealed[name]
        current_time = self._revealed_time[name]
        if not extend_to_panel and target_beat <= current_beat and (
            hold_through_time is None or hold_through_time <= current_time
        ):
            return empty

        trace_group = self._trace_group_for(trace_index)
        previous_keys = self._segment_snapshots[name]
        existing_lines = self._line_children(trace_group)

        new_segments = self._line_segments(
            trace,
            trace_index,
            target_beat,
            extend_to_panel=extend_to_panel,
            hold_through_time=hold_through_time,
        )
        new_keys = tuple(_segment_key(line) for line in new_segments)

        if new_keys == previous_keys:
            return SegmentRevealPlan(trace_group=trace_group)

        first_change = len(new_keys)
        for index in range(min(len(previous_keys), len(new_keys))):
            if new_keys[index] != previous_keys[index]:
                first_change = index
                break
        else:
            if len(new_keys) > len(previous_keys):
                first_change = len(previous_keys)

        if (
            first_change == 0
            and existing_lines
            and new_segments
            and _is_horizontal_extension(existing_lines[0], new_segments[0])
        ):
            _extend_line_in_place(existing_lines[0], new_segments[0])
            first_change = 1

        removed = tuple(existing_lines[first_change:])
        for line in removed:
            trace_group.remove(line)

        added: list[Line] = []
        for line in new_segments[first_change:]:
            line.set_stroke(
                color=trace_color(trace),
                width=theme.WAVEFORM_STROKE_WIDTH,
                opacity=0.0,
            )
            prepare_stroke_reveal((line,))
            added.append(line)

        self._revealed[name] = max(current_beat, target_beat)
        if hold_through_time is not None:
            self._revealed_time[name] = max(self._revealed_time[name], hold_through_time)
        self._segment_snapshots[name] = new_keys

        return SegmentRevealPlan(
            trace_group=trace_group,
            added=tuple(added),
            removed=removed,
        )

    def finalize_reveal(self, signal: Signal) -> tuple[object, ...]:
        """Extend the trace hold line to the panel edge after progressive reveal."""
        name = signal.name
        if name not in self._revealed or self._revealed[name] < 0:
            return ()
        trace = self._bundle.traces[self._trace_index_for(name)]
        if trace.is_discrete:
            plan = self._sync_trace_to_time(
                name,
                target_beat=self._revealed[name],
                extend_to_panel=True,
            )
        else:
            hold_time = max(0.0, self._revealed_time[name])
            plan = self._sync_trace_to_time(
                name,
                hold_through_time=hold_time,
                extend_to_panel=True,
            )
        mount_reveal_plan(plan)
        return plan.added

    def finalize_hold_to_panel(self) -> tuple[object, ...]:
        """Extend each trace's current reveal to the panel edge; return segments for ``Create``."""
        added: list[object] = []
        for trace in self._bundle.traces:
            name = trace.signal_name
            if not self._segment_snapshots[name] and self._revealed[name] < 0:
                continue
            if self._revealed[name] < 0:
                added.extend(self._extend_idle_hold_to_panel(name))
            elif trace.is_discrete:
                plan = self._sync_trace_to_time(
                    name,
                    target_beat=self._revealed[name],
                    extend_to_panel=True,
                )
                mount_reveal_plan(plan)
                added.extend(plan.added)
            else:
                hold_time = max(0.0, self._revealed_time[name])
                plan = self._sync_trace_to_time(
                    name,
                    hold_through_time=hold_time,
                    extend_to_panel=True,
                )
                mount_reveal_plan(plan)
                added.extend(plan.added)
        return tuple(added)

    def _extend_idle_hold_to_panel(self, name: str) -> tuple[object, ...]:
        trace_index = self._trace_index_for(name)
        trace = self._bundle.traces[trace_index]
        trace_group = self._trace_group_for(trace_index)
        previous_keys = self._segment_snapshots[name]
        existing_lines = self._line_children(trace_group)

        new_segments = self._line_segments(
            trace,
            trace_index,
            -1,
            idle_only=True,
            extend_to_panel=True,
        )
        new_keys = tuple(_segment_key(line) for line in new_segments)
        if new_keys == previous_keys:
            return ()

        first_change = 0
        if (
            existing_lines
            and new_segments
            and _is_horizontal_extension(existing_lines[0], new_segments[0])
        ):
            _extend_line_in_place(existing_lines[0], new_segments[0])
            first_change = 1

        removed = existing_lines[first_change:]
        for line in removed:
            trace_group.remove(line)

        to_animate: list[object] = []
        label = trace_group.submobjects[-1]
        trace_group.remove(label)
        for line in new_segments[first_change:]:
            prepare_stroke_reveal((line,))
            line.set_stroke(
                color=trace_color(trace),
                width=theme.WAVEFORM_STROKE_WIDTH,
                opacity=0.0,
            )
            to_animate.append(line)
            trace_group.add(line)
        trace_group.add(label)
        self._segment_snapshots[name] = new_keys
        return tuple(to_animate)

    def reveal_all(self) -> tuple[object, ...]:
        """Extend current reveal to panel edge without adding untaught edges."""
        return self.finalize_hold_to_panel()

    def _line_children(self, trace_group: VGroup) -> list[object]:
        return list(trace_group.submobjects[:-1])

    def _line_segments(
        self,
        trace: WaveformTrace,
        trace_index: int,
        max_beat: int,
        *,
        idle_only: bool = False,
        extend_to_panel: bool = False,
        hold_through_time: float | None = None,
    ) -> list[Line]:
        points = polyline_for_trace(
            trace,
            self._spec,
            trace_index,
            max_beat=max_beat if max_beat >= 0 else None,
            idle_only=idle_only,
            extend_to_panel=extend_to_panel,
            hold_through_time=hold_through_time,
        )
        color = trace_color(trace)
        segments: list[Line] = []
        for start, end in zip(points, points[1:], strict=False):
            if start.x == end.x and start.y == end.y:
                continue
            segments.append(
                Line(
                    point3(start),
                    point3(end),
                    stroke_color=color,
                    stroke_width=theme.WAVEFORM_STROKE_WIDTH,
                )
            )
        return segments

def mount_reveal_plan(plan: SegmentRevealPlan) -> tuple[Line, ...]:
    """Insert planned segments into the trace group (before ``Create`` in the same beat)."""
    if not plan.added:
        return ()
    trace_group = plan.trace_group
    if not trace_group.submobjects:
        return plan.added
    label = trace_group.submobjects[-1]
    trace_group.remove(label)
    for line in plan.added:
        trace_group.add(line)
    trace_group.add(label)
    return plan.added


def _segment_key(line: Line) -> _SegmentKey:
    start = line.get_start()
    end = line.get_end()
    return (
        round(float(start[0]), 6),
        round(float(start[1]), 6),
        round(float(end[0]), 6),
        round(float(end[1]), 6),
    )


def _is_horizontal_extension(existing: Line, proposed: Line) -> bool:
    es, ee = existing.get_start(), existing.get_end()
    ps, pe = proposed.get_start(), proposed.get_end()
    if abs(float(es[1]) - float(ee[1])) > 1e-6 or abs(float(ps[1]) - float(pe[1])) > 1e-6:
        return False
    if abs(float(es[0]) - float(ps[0])) > 1e-6 or abs(float(es[1]) - float(ps[1])) > 1e-6:
        return False
    return float(pe[0]) >= float(ee[0]) - 1e-6


def _extend_line_in_place(line: Line, target: Line) -> None:
    line.put_start_and_end_on(target.get_start(), target.get_end())


def commit_beat_reveal(lines: tuple[object, ...]) -> None:
    """Persist trace visibility after beat ``Create`` (centralized; not on beat module)."""
    restore_waveform_strokes(lines)
