"""Waveform-centric teaching scene template (fixture + construct orchestration)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from manim import Create, FadeIn, FadeOut, LaggedStart, Scene, VGroup, Write

if TYPE_CHECKING:
    from manim import Text

from manim_engineering.animation.hud import (
    CaptionTrack,
    intro_safe_hud_copy,
    make_caption_track,
    play_hud_intro,
)
from manim_engineering.animation.intro_plan import IntroPlan, build_intro_plan
from manim_engineering.animation.intro_style import IntroStyle
from manim_engineering.animation.label_phase import (
    LabelPhasePolicy,
    label_allowed_in_phase,
)
from manim_engineering.animation.pacing import (
    INTRO_PAUSE,
    OUTRO_PAUSE,
    SCENE_FADE_OUT,
    scene_final_fade_enabled,
)
from manim_engineering.animation.propagation_sequence import BeatSpec, PropagationSequence
from manim_engineering.animation.scene import (
    SceneCamera,
    configure_topology_scene_camera,
    configure_waveform_scene_camera,
)
from manim_engineering.animation.scene_mobjects import scene_display_mobjects
from manim_engineering.animation.scene_template import (
    _iter_trace_line_strokes,
    play_topology_intro,
    play_waveform_idle_baseline,
)
from manim_engineering.animation.style import TeachingStyle
from manim_engineering.animation.trace import flush_trace, maybe_snapshot_stage, reset_tracer
from manim_engineering.animation.waveform_controller import WaveformSegmentController
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.components import CircuitElement
from manim_engineering.core import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer
from manim_engineering.renderers.minimal.labels import (
    detach_label_roots,
    hide_labels,
    iter_label_roots,
    label_role,
    label_visible,
    refresh_label_strokes,
    restore_waveform_strokes,
    set_label_visible,
)
from manim_engineering.semantic import Signal
from manim_engineering.waveform.trace import WaveformBundle

DEFAULT_HUD_SUBTITLE_BAND = 1.25


def _label_is_visible(label: VGroup) -> bool:
    return label_visible(label)


def _refresh_static_scene_background(scene: Scene) -> None:
    renderer = getattr(scene, "renderer", None)
    save_static = getattr(renderer, "save_static_frame_data", None)
    if callable(save_static):
        save_static(scene, scene_display_mobjects(scene))


def _play_label_reveal(
    scene: Scene,
    *roots: VGroup,
    roles: tuple[str, ...] | None = None,
    role_prefixes: tuple[str, ...] = (),
    policy: LabelPhasePolicy | None = None,
    phase: str | None = None,
    mode: Literal["fade", "write"] = "fade",
    run_time: float = 0.24,
    lag_ratio: float = 0.12,
) -> None:
    labels = [
        label
        for root in roots
        for label in iter_label_roots(root, roles=roles)
        if not role_prefixes
        or any(
            (label_role(label) or "").startswith(prefix)
            for prefix in role_prefixes
        )
        if phase is None or label_allowed_in_phase(label, phase, policy)
        if not _label_is_visible(label)
    ]
    if not labels:
        return
    for root in roots:
        root.remove(*labels)
    revealed = []
    for label in labels:
        fresh = label.copy()
        set_label_visible(fresh, True)
        refresh_label_strokes(fresh, mode="full")
        fresh.set_opacity(0.0)
        revealed.append(fresh)
    scene.add(*revealed)
    animation_cls = Write if mode == "write" else FadeIn
    if len(revealed) == 1:
        scene.play(animation_cls(revealed[0]), run_time=run_time)
    else:
        scene.play(
            LaggedStart(
                *[animation_cls(label) for label in revealed],
                lag_ratio=lag_ratio,
            ),
            run_time=run_time,
        )
    for label in revealed:
        refresh_label_strokes(label, mode="full")


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
    4. Play the 3B1B-style intro via :meth:`play_intro` (default: :func:`play_topology_intro`).
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

    intro_components_run_time: float | None = None
    intro_wires_run_time: float | None = None
    intro_panel_run_time: float | None = None
    intro_lag_ratio: float = 0.15
    intro_total_run_time: float | None = None
    intro_pause_offset: float = 0.5
    play_waveform_baseline: bool = True
    baseline_traces: frozenset[str] | None = None
    """When set, only these signal names receive idle stub ``Create``; ``None`` = all traces."""
    extend_waveform_to_panel: bool = False
    """When ``False``, beats stop at last taught time — no silent finalize hold to panel edge."""
    baseline_run_time: float = 0.4
    """Subtracted from ``INTRO_PAUSE`` for the post-stage hold; HUD demos
    typically use 0.6 to account for the title+intro plays."""
    annotation_run_time: float = 0.24
    annotation_net_run_time: float = 0.18
    pin_label_intro_mode: Literal["fade", "write"] = "fade"
    """How interface pin labels reveal during intro annotations."""

    style: TeachingStyle = TeachingStyle()
    """Scene-level animation tuning passed to beats and HUD crossfades."""

    intro_style: IntroStyle = IntroStyle()
    """Topology intro: Line ``Create`` vs Polygon ``DrawBorderThenFill``."""

    @abstractmethod
    def build_fixture(self) -> WaveformFixture:
        """Return the demo fixture (graph, layout, bundle, signals)."""

    def teaching_beats(self, fixture: WaveformFixture) -> tuple[BeatSpec, ...] | None:
        return None

    def hud_texts(self, fixture: WaveformFixture) -> tuple[str, str] | None:
        return None

    def hud_intro_texts(self, fixture: WaveformFixture) -> tuple[str, str] | None:
        """Opening HUD copy; defaults to an intro-safe fallback derived from ``hud_texts``."""
        return intro_safe_hud_copy(self.hud_texts(fixture))

    def propagation_options(self) -> dict:
        return {}

    def label_phase_policy(self) -> LabelPhasePolicy:
        return LabelPhasePolicy()

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

    def play_intro(
        self,
        topology: object,
        waveform_panel: VGroup,
        content: VGroup,
    ) -> None:
        """Play topology intro; waveform traces reveal separately via baseline play."""
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
            include_panel_traces=False,
            intro_style=self.intro_style,
            intro_plan=self.build_intro_plan(topology, waveform_panel),
            reveal_component_labels=False,
            reveal_net_labels=False,
            reveal_panel_labels=False,
        )

    def build_intro_plan(
        self,
        topology: object,
        waveform_panel: VGroup,
    ) -> IntroPlan:
        return build_intro_plan(
            topology,
            waveform_panel,
            components_run_time=self.intro_components_run_time,
            wires_run_time=self.intro_wires_run_time,
            panel_run_time=self.intro_panel_run_time,
            include_panel_traces=False,
        )

    def play_waveform_baseline_intro(
        self,
        waveform_panel: VGroup,
        waveform_controller: WaveformSegmentController,
        *,
        bundle: WaveformBundle | None = None,
    ) -> None:
        """Reveal idle trace baselines before the first propagation beat."""
        if not self.play_waveform_baseline:
            restore_waveform_strokes(_iter_trace_line_strokes(waveform_panel))
            waveform_controller.sync_idle_baselines()
            return
        play_waveform_idle_baseline(
            self,
            waveform_panel,
            run_time=self.baseline_run_time,
            lag_ratio=self.intro_lag_ratio,
            baseline_traces=self.baseline_traces,
            bundle=bundle,
        )
        waveform_controller.sync_idle_baselines(self.baseline_traces)

    def finalize_waveform(
        self,
        waveform_controller: WaveformSegmentController,
        fixture: WaveformFixture,
    ) -> tuple[object, ...]:
        """Optionally extend revealed traces to the panel edge after the beat sequence."""
        _ = fixture
        if not self.extend_waveform_to_panel:
            return ()
        return waveform_controller.finalize_hold_to_panel()

    def play_intro_annotations(
        self,
        topology_labels: VGroup,
        waveform_panel_labels: VGroup,
    ) -> None:
        policy = self.label_phase_policy()
        _play_label_reveal(
            self,
            topology_labels,
            waveform_panel_labels,
            roles=("component_label",),
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            roles=("net_label",),
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_net_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            role_prefixes=("interface.pin.",),
            policy=policy,
            phase="intro_annotation",
            mode=self.pin_label_intro_mode,
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            waveform_panel_labels,
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )

    def construct(self) -> None:
        reset_tracer()
        fixture = self.build_fixture()
        hud = self.hud_intro_texts(fixture)

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
        waveform_controller = WaveformSegmentController(reveal_tracker)
        topology_labels = VGroup(*detach_label_roots(topology.components))
        waveform_panel_labels = VGroup(*detach_label_roots(waveform_panel))
        hide_labels(topology_labels)
        hide_labels(waveform_panel_labels)
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

        self.play_intro(topology, waveform_panel, content)
        maybe_snapshot_stage(self, "01_after_intro")

        caption_track: CaptionTrack | None = None
        title_mob: Text | None = None
        if hud is not None:
            title_text, intro_text = hud
            title_mob, intro_mob = play_hud_intro(self, title_text, intro_text, camera)
            caption_track = make_caption_track(
                self,
                intro_mob,
                camera,
                title=title_mob,
                crossfade=self.style.caption_crossfade,
            )

        self.play_intro_annotations(topology_labels, waveform_panel_labels)
        self.after_intro_hook(fixture, camera)
        self.play_waveform_baseline_intro(
            waveform_panel,
            waveform_controller,
            bundle=fixture.bundle,
        )
        _refresh_static_scene_background(self)
        self.wait(max(INTRO_PAUSE - self.intro_pause_offset, 0.3))

        beats = self.teaching_beats(fixture)
        if beats:
            options = dict(self.propagation_options())
            if self.dim_inactive:
                options.setdefault("dim_inactive", True)

            sequence = PropagationSequence(
                layout=fixture.layout,
                graph=fixture.graph,
                beats=beats,
                bundle=fixture.bundle,
                sync_signals=fixture.signals,
                panel_spec=panel_spec,
                beat_duration=self.style.beat_duration,
                beat_gap=self.style.beat_gap,
                topology=topology,
                label_layer=topology_labels,
                caption_callback=caption_track.swap if caption_track is not None else None,
                waveform_controller=waveform_controller,
                label_phase_policy=self.label_phase_policy(),
                style=self.style,
                **options,
            )
            sequence.play(self)
            pending = self.finalize_waveform(waveform_controller, fixture)
            if pending:
                if len(pending) == 1:
                    self.play(Create(pending[0]), run_time=self.baseline_run_time)
                else:
                    self.play(
                        LaggedStart(*[Create(line) for line in pending], lag_ratio=0.1),
                        run_time=self.baseline_run_time,
                    )
                restore_waveform_strokes(pending)
            maybe_snapshot_stage(self, "99_after_beats")

        if caption_track is not None:
            caption_track.close()

        self.wait(max(OUTRO_PAUSE - SCENE_FADE_OUT, 0.2))
        self.after_beats_hook(fixture, camera)

        if scene_final_fade_enabled():
            self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))
        else:
            self.wait(SCENE_FADE_OUT)
        flush_trace(self)


@dataclass(frozen=True)
class TopologyFixture:
    """Per-demo data for :class:`TopologyTeachingScene` (no waveform panel)."""

    graph: CircuitGraph
    elements: Mapping[str, CircuitElement]
    layout: LayoutResult


class TopologyTeachingScene(Scene, ABC):
    """Template for topology-only teaching demos (intro + HUD + hold, no beats).

    Use when a catalog example has no ``WaveformBundle`` / propagation beats.
    """

    subtitle_band: float | None = None
    camera_target_fill: float = 0.70

    intro_components_run_time: float | None = None
    intro_wires_run_time: float | None = None
    intro_panel_run_time: float = 0.0
    intro_lag_ratio: float = 0.15
    intro_total_run_time: float | None = None
    intro_pause_offset: float = 0.5

    style: TeachingStyle = TeachingStyle()
    intro_style: IntroStyle = IntroStyle()
    annotation_run_time: float = 0.24
    annotation_net_run_time: float = 0.18
    pin_label_intro_mode: Literal["fade", "write"] = "fade"
    """How interface pin labels reveal during intro annotations."""

    @abstractmethod
    def build_fixture(self) -> TopologyFixture:
        """Return graph, layout, and elements for this demo."""

    def hud_texts(self, fixture: TopologyFixture) -> tuple[str, str] | None:
        return None

    def hud_intro_texts(self, fixture: TopologyFixture) -> tuple[str, str] | None:
        """Opening HUD copy; defaults to an intro-safe fallback derived from ``hud_texts``."""
        return intro_safe_hud_copy(self.hud_texts(fixture))

    def render_topology(self, fixture: TopologyFixture):
        """Override to pass renderer options (e.g. MOSFET convention)."""
        return ManimRenderer().render_topology(
            fixture.graph,
            fixture.layout,
            dict(fixture.elements),
        )

    def label_phase_policy(self) -> LabelPhasePolicy:
        return LabelPhasePolicy()

    def after_intro_hook(
        self,
        fixture: TopologyFixture,
        camera: SceneCamera,
    ) -> None:
        """Called after intro/HUD, before the post-intro hold."""

    def after_hold_hook(
        self,
        fixture: TopologyFixture,
        camera: SceneCamera,
    ) -> None:
        """Called after the intro hold, before optional ``FadeOut``."""

    def play_intro(
        self,
        topology: object,
        waveform_panel: VGroup,
        content: VGroup,
    ) -> None:
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
            intro_style=self.intro_style,
            intro_plan=self.build_intro_plan(topology, waveform_panel),
            reveal_component_labels=False,
            reveal_net_labels=False,
            reveal_panel_labels=False,
        )

    def build_intro_plan(
        self,
        topology: object,
        waveform_panel: VGroup,
    ) -> IntroPlan:
        return build_intro_plan(
            topology,
            waveform_panel,
            components_run_time=self.intro_components_run_time,
            wires_run_time=self.intro_wires_run_time,
            panel_run_time=self.intro_panel_run_time,
            include_panel_traces=False,
        )

    def play_intro_annotations(
        self,
        topology_labels: VGroup,
        waveform_panel_labels: VGroup,
    ) -> None:
        policy = self.label_phase_policy()
        _play_label_reveal(
            self,
            topology_labels,
            waveform_panel_labels,
            roles=("component_label",),
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            roles=("net_label",),
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_net_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            role_prefixes=("interface.pin.",),
            policy=policy,
            phase="intro_annotation",
            mode=self.pin_label_intro_mode,
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )
        _play_label_reveal(
            self,
            topology_labels,
            waveform_panel_labels,
            policy=policy,
            phase="intro_annotation",
            run_time=self.annotation_run_time,
            lag_ratio=self.intro_lag_ratio,
        )

    def construct(self) -> None:
        reset_tracer()
        fixture = self.build_fixture()
        hud = self.hud_intro_texts(fixture)

        topology = self.render_topology(fixture)
        topology_labels = VGroup(*detach_label_roots(topology.components))
        hide_labels(topology_labels)
        empty_panel = VGroup()
        content = VGroup(topology.components, topology.wires)

        camera = configure_topology_scene_camera(
            self,
            fixture.layout,
            target_fill=self.camera_target_fill,
            subtitle_band=(
                self.subtitle_band
                if self.subtitle_band is not None
                else (DEFAULT_HUD_SUBTITLE_BAND if hud is not None else 0.0)
            ),
        )

        self.play_intro(topology, empty_panel, content)
        maybe_snapshot_stage(self, "01_after_intro")

        caption_track: CaptionTrack | None = None
        if hud is not None:
            title_text, intro_text = hud
            title_mob, intro_mob = play_hud_intro(self, title_text, intro_text, camera)
            caption_track = make_caption_track(
                self,
                intro_mob,
                camera,
                title=title_mob,
                crossfade=self.style.caption_crossfade,
            )

        self.play_intro_annotations(topology_labels, empty_panel)
        self.after_intro_hook(fixture, camera)
        _refresh_static_scene_background(self)
        self.wait(max(INTRO_PAUSE - self.intro_pause_offset, 0.3))

        if caption_track is not None:
            caption_track.close()

        self.wait(max(OUTRO_PAUSE - SCENE_FADE_OUT, 0.2))
        self.after_hold_hook(fixture, camera)

        if scene_final_fade_enabled():
            self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))
        else:
            self.wait(SCENE_FADE_OUT)
        flush_trace(self)
