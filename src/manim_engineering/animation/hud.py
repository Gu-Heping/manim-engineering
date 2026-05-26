"""Teaching HUD: title, intro, and per-beat caption crossfades."""

from __future__ import annotations

from manim import AnimationGroup, FadeIn, FadeOut, Text

from manim_engineering.animation.layers import HUD_Z_INDEX
from manim_engineering.animation.pacing import CAPTION_CROSSFADE, subtitle_text
from manim_engineering.animation.propagation_sequence import BeatSpec
from manim_engineering.animation.scene import SceneCamera
from manim_engineering.animation.scene_protocol import (
    TeachingSceneProtocol,
    require_scene_methods,
)
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
        seed: Text,
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
        record_stage(
            "hud.caption",
            beat_index=index,
            signal_name=spec.signal.name,
            run_time=crossfade,
            caption_len=len(spec.caption),
        )

    def close(self) -> None:
        if self.current is not None:
            self._scene.play(FadeOut(self.current, run_time=self._crossfade))
            self._scene.remove(self.current)
            self.current = None


def play_hud_intro(
    scene: TeachingSceneProtocol,
    title_text: str,
    intro_text: str,
    camera: SceneCamera,
) -> tuple[Text, Text]:
    """Play the 3B1B-style HUD intro: ``FadeIn(title)`` then ``FadeIn(intro)``.

    Returns the two ``Text`` mobjects so the caller can keep references for
    later (e.g. seeding a :class:`CaptionTrack` or fading out at the end).
    """
    scene = require_scene_methods(scene, require_play=True)
    title = subtitle_text(title_text, role="title")
    intro = subtitle_text(intro_text, role="intro")
    title.move_to([camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=0), 0])
    intro.move_to([camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=1), 0])
    title.set_z_index(HUD_Z_INDEX)
    intro.set_z_index(HUD_Z_INDEX)
    scene.play(FadeIn(title, shift=0.08), run_time=0.5)
    scene.play(FadeIn(intro, shift=0.15), run_time=0.55)
    record_stage("hud.intro", run_time=1.05, title_len=len(title_text), intro_len=len(intro_text))
    return title, intro


def make_caption_track(
    scene: TeachingSceneProtocol,
    seed: Text,
    camera: SceneCamera,
    *,
    title: Text | None = None,
    crossfade: float = CAPTION_CROSSFADE,
) -> CaptionTrack:
    """Return a :class:`CaptionTrack` whose ``swap`` matches the
    :class:`PropagationSequence.caption_callback` protocol."""
    return CaptionTrack(scene, seed, camera, title=title, crossfade=crossfade)
