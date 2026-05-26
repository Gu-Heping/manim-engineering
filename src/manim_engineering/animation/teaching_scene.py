"""Waveform-centric teaching scene template (fixture + construct orchestration)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from manim import FadeOut, Scene, VGroup

if TYPE_CHECKING:
    from manim import Text

from manim_engineering.animation.hud import CaptionTrack, make_caption_track, play_hud_intro
from manim_engineering.animation.pacing import (
    BEAT_GAP,
    INTRO_PAUSE,
    OUTRO_PAUSE,
    SCENE_FADE_OUT,
    scene_final_fade_enabled,
)
from manim_engineering.animation.propagation_sequence import BeatSpec, PropagationSequence
from manim_engineering.animation.scene import SceneCamera, configure_waveform_scene_camera
from manim_engineering.animation.scene_template import play_topology_intro
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.components import CircuitElement
from manim_engineering.core import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.semantic import Signal
from manim_engineering.waveform.trace import WaveformBundle

DEFAULT_HUD_SUBTITLE_BAND = 1.25


@dataclass(frozen=True)
class WaveformFixture:
    """Per-demo data the :class:`WaveformDemoScene` template needs."""

    graph: CircuitGraph
    elements: Mapping[str, CircuitElement]
    layout: LayoutResult
    bundle: WaveformBundle
    signals: tuple[Signal, ...] = field(default_factory=tuple)


class WaveformDemoScene(Scene, ABC):
    """Template-method base for waveform-centric teaching demos.

    Subclasses must implement :meth:`build_fixture`. The default
    :meth:`construct` orchestrates:

    1. Build a :class:`WaveformFixture` via :meth:`build_fixture`.
    2. Render topology + waveform panel with :class:`ManimRenderer` /
       :class:`WaveformPanelRenderer`.
    3. Configure camera via :func:`configure_waveform_scene_camera`, using
       :attr:`subtitle_band` for HUD reservation.
    4. Play the 3B1B-style intro via :func:`play_topology_intro`.
    5. Optionally play the HUD intro (``FadeIn(title)`` + ``FadeIn(intro)``)
       when :meth:`hud_texts` returns a non-``None`` ``(title, intro)`` pair.
    6. Optionally play a :class:`PropagationSequence` when
       :meth:`teaching_beats` returns a non-``None`` tuple of beats.
    7. Call :meth:`after_beats_hook` (a no-op by default).
    8. Fade out under :func:`scene_final_fade_enabled` control.
    """

    subtitle_band: float | None = None
    """If set, reserves vertical space for HUD rows above the topology."""

    camera_target_fill: float = 0.70
    """Passed to :func:`configure_waveform_scene_camera` as ``target_fill``."""

    dim_inactive: bool = False
    """If ``True`` and :meth:`teaching_beats` returns beats, the topology is
    dimmed between beats (default :class:`PropagationSequence` keeps it lit)."""

    intro_components_run_time: float = 0.6
    intro_wires_run_time: float = 0.5
    intro_panel_run_time: float = 0.6
    intro_lag_ratio: float = 0.25
    intro_total_run_time: float = 1.3
    intro_pause_offset: float = 0.5
    """Subtracted from ``INTRO_PAUSE`` for the post-stage hold; HUD demos
    typically use 0.6 to account for the title+intro plays."""

    @abstractmethod
    def build_fixture(self) -> WaveformFixture:
        """Return the demo fixture (graph, layout, bundle, signals)."""

    def teaching_beats(self, fixture: WaveformFixture) -> tuple[BeatSpec, ...] | None:
        return None

    def hud_texts(self, fixture: WaveformFixture) -> tuple[str, str] | None:
        return None

    def propagation_options(self) -> dict:
        return {}

    def after_intro_hook(
        self,
        fixture: WaveformFixture,
        camera: SceneCamera,
    ) -> None:
        """Called after the intro (and HUD play) but *before* the post-intro hold."""

    def after_beats_hook(
        self,
        fixture: WaveformFixture,
        camera: SceneCamera,
    ) -> None:
        """Called after beats/outro hold, *before* the optional ``FadeOut``."""

    def construct(self) -> None:
        fixture = self.build_fixture()
        hud = self.hud_texts(fixture)

        topology = ManimRenderer().render_topology(
            fixture.graph, fixture.layout, dict(fixture.elements)
        )
        panel_renderer = WaveformPanelRenderer()
        waveform_panel, panel_spec = panel_renderer.render_with_layout(
            fixture.bundle, fixture.layout, idle_only=True
        )
        reveal_tracker = WaveformRevealTracker(
            waveform_panel, fixture.bundle, panel_spec, panel_renderer
        )
        content = VGroup(topology.components, topology.wires, waveform_panel)

        camera = configure_waveform_scene_camera(
            self,
            fixture.layout,
            panel_spec,
            fixture.bundle,
            target_fill=self.camera_target_fill,
            subtitle_band=(
                self.subtitle_band
                if self.subtitle_band is not None
                else (DEFAULT_HUD_SUBTITLE_BAND if hud is not None else 0.0)
            ),
        )

        play_topology_intro(
            self,
            topology,
            waveform_panel,
            content,
            components_run_time=self.intro_components_run_time,
            wires_run_time=self.intro_wires_run_time,
            panel_run_time=self.intro_panel_run_time,
            lag_ratio=self.intro_lag_ratio,
            total_run_time=self.intro_total_run_time,
        )

        caption_track: CaptionTrack | None = None
        title_mob: Text | None = None
        if hud is not None:
            title_text, intro_text = hud
            title_mob, intro_mob = play_hud_intro(self, title_text, intro_text, camera)
            caption_track = make_caption_track(self, intro_mob, camera, title=title_mob)

        self.after_intro_hook(fixture, camera)
        self.wait(max(INTRO_PAUSE - self.intro_pause_offset, 0.3))

        beats = self.teaching_beats(fixture)
        if beats:
            options = dict(self.propagation_options())
            if self.dim_inactive:
                options.setdefault("dim_inactive", True)
                options.setdefault("topology", topology)

            sequence = PropagationSequence(
                layout=fixture.layout,
                graph=fixture.graph,
                beats=beats,
                bundle=fixture.bundle,
                sync_signals=fixture.signals,
                panel_spec=panel_spec,
                beat_gap=BEAT_GAP,
                caption_callback=caption_track.swap if caption_track is not None else None,
                reveal_tracker=reveal_tracker,
                **options,
            )
            sequence.play(self)
            reveal_tracker.reveal_all()

        if caption_track is not None:
            caption_track.close()

        self.wait(max(OUTRO_PAUSE - SCENE_FADE_OUT, 0.2))
        self.after_beats_hook(fixture, camera)

        if scene_final_fade_enabled():
            self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))
        else:
            self.wait(SCENE_FADE_OUT)
