"""Teaching HUD: title, intro, and per-beat caption crossfades."""

from __future__ import annotations

from manim import AnimationGroup, FadeIn, FadeOut, Text

from manim_engineering.animation.layers import HUD_Z_INDEX
from manim_engineering.animation.pacing import CAPTION_CROSSFADE, subtitle_text
from manim_engineering.animation.propagation_sequence import BeatSpec
from manim_engineering.animation.scene import SceneCamera
from manim_engineering.animation.scene_mobjects import scene_display_mobjects
from manim_engineering.animation.scene_protocol import (
    TeachingSceneProtocol,
    require_scene_methods,
)
from manim_engineering.animation.stage_record import record_plain_stage
from manim_engineering.animation.trace import record_stage
from manim_engineering.waveform import hud_text_y


class CaptionTrack:
    """Maintain a single on-screen caption mobject across multiple beats.

    The :meth:`swap` method is plugged into
    :class:`PropagationSequence.caption_callback`. After the beat sequence
    completes, call :meth:`close` to fade out the last caption.
    """

    def __init__(
        self,
        scene: TeachingSceneProtocol,
        seed: Text | None,
        camera: SceneCamera,
        *,
        title: Text | None = None,
        crossfade: float = CAPTION_CROSSFADE,
    ) -> None:
        scene = require_scene_methods(scene, require_play=True, require_remove=True)
        self._scene = scene
        self._camera = camera
        self.current: Text | None = seed
        self._title: Text | None = title
        self._crossfade = crossfade

    def swap(self, spec: BeatSpec, index: int) -> None:
        if not spec.caption:
            return
        next_caption = subtitle_text(spec.caption, role="caption")
        next_caption.move_to(
            [
                self._camera.frame_cx,
                hud_text_y(self._camera.frame_cy, self._camera.frame_height, row=1),
                0,
            ]
        )
        next_caption.set_z_index(HUD_Z_INDEX)
        current = self.current
        crossfade = self._crossfade
        to_remove: list[Text] = []
        animations: list[object] = []
        if index == 0 and self._title is not None:
            animations.append(FadeOut(self._title, run_time=crossfade))
            to_remove.append(self._title)
            self._title = None
        if current is not None:
            animations.append(FadeOut(current, run_time=crossfade))
            to_remove.append(current)
        animations.append(FadeIn(next_caption, run_time=crossfade))
        if len(animations) == 1:
            self._scene.play(animations[0], run_time=crossfade)
        else:
            self._scene.play(AnimationGroup(*animations), run_time=crossfade)
        if to_remove:
            self._scene.remove(*to_remove)
        self.current = next_caption
        record_plain_stage(
            "hud.caption",
            run_time=crossfade,
            beat_index=index,
            signal_name=spec.signal.name,
            caption_len=len(spec.caption),
            record=record_stage,
        )

    def close(self) -> None:
        if self.current is not None:
            self._scene.play(FadeOut(self.current, run_time=self._crossfade))
            self._scene.remove(self.current)
            self.current = None


def play_hud_intro(
    scene: TeachingSceneProtocol,
    title_text: str,
    intro_text: str | None,
    camera: SceneCamera,
) -> tuple[Text, Text | None]:
    """Play the 3B1B-style HUD intro: ``FadeIn(title)`` then ``FadeIn(intro)``.

    Returns the HUD ``Text`` mobjects so the caller can keep references for
    later (e.g. seeding a :class:`CaptionTrack` or fading out at the end).
    """
    scene = require_scene_methods(scene, require_play=True)
    renderer = getattr(scene, "renderer", None)
    save_static = getattr(renderer, "save_static_frame_data", None)
    if callable(save_static):
        save_static(scene, scene_display_mobjects(scene))
    title = subtitle_text(title_text, role="title")
    title.move_to([camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=0), 0])
    title.set_z_index(HUD_Z_INDEX)
    title.set_opacity(0.0)
    scene.add(title)
    title_run_time = 0.5
    scene.play(title.animate.set_opacity(1.0), run_time=title_run_time)
    intro: Text | None = None
    intro_run_time = 0.0
    if intro_text:
        intro = subtitle_text(intro_text, role="intro")
        intro.move_to(
            [camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=1), 0]
        )
        intro.set_z_index(HUD_Z_INDEX)
        intro.set_opacity(0.0)
        scene.add(intro)
        intro_run_time = 0.55
        scene.play(intro.animate.set_opacity(1.0), run_time=intro_run_time)
    record_plain_stage(
        "hud.intro",
        run_time=title_run_time + intro_run_time,
        title_len=len(title_text),
        intro_len=len(intro_text or ""),
        record=record_stage,
    )
    return title, intro


def intro_safe_hud_copy(hud: tuple[str, str] | None) -> tuple[str, str] | None:
    """Default opening HUD copy derived from the canonical scene HUD text.

    Opening HUD should establish context without preemptively narrating the
    full signal path or conclusion. By default, keep only the title prefix
    before the common ``·`` separator and omit the second line entirely.
    """
    if hud is None:
        return None
    title_text, _intro_text = hud
    title_prefix = title_text.strip()
    for separator in (" · ", "·", " 路 "):
        if separator in title_prefix:
            title_prefix = title_prefix.split(separator, 1)[0].strip()
            break
    return title_prefix, ""


def make_caption_track(
    scene: TeachingSceneProtocol,
    seed: Text | None,
    camera: SceneCamera,
    *,
    title: Text | None = None,
    crossfade: float = CAPTION_CROSSFADE,
) -> CaptionTrack:
    """Return a :class:`CaptionTrack` whose ``swap`` matches the
    :class:`PropagationSequence.caption_callback` protocol."""
    return CaptionTrack(scene, seed, camera, title=title, crossfade=crossfade)
