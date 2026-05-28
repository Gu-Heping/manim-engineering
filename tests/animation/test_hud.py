"""Teaching HUD stage: caption crossfade and intro."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, FadeIn, FadeOut
from recording_scene import RecordingScene
from scene_trace import played_role_sets

from manim_engineering.animation import (
    CAPTION_CROSSFADE,
    HUD_Z_INDEX,
    BeatSpec,
    CaptionTrack,
    SceneCamera,
    play_hud_intro,
    subtitle_text,
)
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal.labels import label_role
from manim_engineering.semantic import LogicLevel, LogicState, Signal


def _camera() -> SceneCamera:
    return SceneCamera(frame_width=14.0, frame_height=8.0, frame_cx=0.0, frame_cy=0.0)


def _beat_spec(*, caption: str | None = "caption") -> BeatSpec:
    graph = CircuitGraph()
    r1 = Resistor("r1")
    r2 = Resistor("r2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    signal = Signal(
        name="s",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    signal.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    return BeatSpec(signal=signal, record=signal.propagation_history[0], caption=caption)


def test_caption_track_swap_no_op_without_caption() -> None:
    scene = RecordingScene()
    seed = subtitle_text("intro", role="intro")
    track = CaptionTrack(scene, seed, _camera())
    track.swap(_beat_spec(caption=None), index=0)
    assert scene.played == []


def test_caption_track_first_beat_fades_title() -> None:
    scene = RecordingScene()
    title = subtitle_text("title", role="title")
    seed = subtitle_text("intro", role="intro")
    track = CaptionTrack(scene, seed, _camera(), title=title)
    track.swap(_beat_spec(caption="beat 0"), index=0)
    assert len(scene.played) == 1
    group = scene.played[0][0]
    assert isinstance(group, AnimationGroup)
    assert scene.run_times[0] == pytest.approx(CAPTION_CROSSFADE)


def test_play_hud_intro_sets_hud_z_index() -> None:
    scene = RecordingScene()
    title, intro = play_hud_intro(scene, "RC 充电", "观察电容电压爬升", _camera())
    assert title.get_z_index() == HUD_Z_INDEX
    assert intro is not None
    assert intro.get_z_index() == HUD_Z_INDEX
    assert len(scene.played) == 2
    assert title in scene.added
    assert intro in scene.added
    assert played_role_sets(scene.played) == [{"hud.title"}, {"hud.intro"}]


def test_play_hud_intro_saves_static_background_before_overlay() -> None:
    scene = RecordingScene()

    class _Renderer:
        def __init__(self) -> None:
            self.calls: list[tuple[object, list[object]]] = []

        def save_static_frame_data(self, scene_obj, static_mobjects) -> None:
            self.calls.append((scene_obj, list(static_mobjects)))

    renderer = _Renderer()
    scene.renderer = renderer
    scene.mobjects = [object(), object()]
    scene.foreground_mobjects = [object()]

    play_hud_intro(scene, "RC 充电", "观察电容电压爬升", _camera())

    assert renderer.calls == [(scene, scene.mobjects + scene.foreground_mobjects)]


def test_subtitle_text_uses_hud_label_role_and_zero_stroke() -> None:
    title = subtitle_text("title", role="title")
    assert label_role(title) == "hud.title"
    for sub in title.get_family():
        if len(sub.points) == 0:
            continue
        assert sub.get_stroke_opacity() == 0.0


def test_play_hud_intro_skips_empty_intro_line() -> None:
    scene = RecordingScene()
    title, intro = play_hud_intro(scene, "RC 鍏呯數", "", _camera())
    assert title.get_z_index() == HUD_Z_INDEX
    assert intro is None
    assert len(scene.played) == 1
    assert played_role_sets(scene.played) == [{"hud.title"}]


def test_caption_crossfade_uses_pacing_constant() -> None:
    scene = RecordingScene()
    seed = subtitle_text("intro", role="intro")
    track = CaptionTrack(scene, seed, _camera())
    track.swap(_beat_spec(caption="next"), index=1)
    assert len(scene.played) == 1
    group = scene.played[0][0]
    assert isinstance(group, AnimationGroup)
    assert scene.run_times[0] == pytest.approx(CAPTION_CROSSFADE)
    anims = group.animations
    assert len(anims) == 2
    assert isinstance(anims[0], FadeOut)
    assert isinstance(anims[1], FadeIn)
