"""Progressive waveform trace reveal synchronized with propagation beats."""

from __future__ import annotations

from manim import VGroup

from manim_engineering.renderers.minimal.waveform import WaveformPanelRenderer
from manim_engineering.semantic.signal import Signal
from manim_engineering.waveform.layout import WaveformPanelSpec
from manim_engineering.waveform.trace import WaveformBundle


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

    def reveal_all(self) -> None:
        """Show full history on every trace (end of sequence)."""
        for trace in self._bundle.traces:
            edges = max(0, len(trace.samples) - 2)
            self._revealed[trace.signal_name] = edges
            self._refresh_trace(trace.signal_name)

    def _refresh_trace(self, signal_name: str) -> None:
        trace_index = next(
            i for i, t in enumerate(self._bundle.traces) if t.signal_name == signal_name
        )
        trace = self._bundle.traces[trace_index]
        max_beat = self._revealed[signal_name]
        new_group = self._renderer.render_trace(
            trace,
            self._spec,
            trace_index,
            max_beat=max_beat if max_beat >= 0 else None,
            idle_only=max_beat < 0,
        )
        self._panel.submobjects[trace_index] = new_group
