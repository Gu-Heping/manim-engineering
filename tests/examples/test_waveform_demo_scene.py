"""Smoke + invariant tests for the shared :class:`WaveformDemoScene` template.

Covers four behaviours, all light-weight (no manim render):
1. :class:`WaveformFixture` is a *frozen* dataclass (immutability guards
   against in-place mutation between intro and beats).
2. A minimal subclass can run ``Scene.render()`` end-to-end without raising.
3. :func:`capture_camera_frame` lands a PNG at the requested path.
4. :class:`CaptionTrack` keeps **exactly one** caption mobject on screen
   after multiple beat swaps (regression guard for the dictionary-state
   closure in the original SPI/UART demos).
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

pytest.importorskip("manim")

_EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"
if str(_EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES_DIR))

import _shared as shared  # noqa: E402
from _shared import (  # noqa: E402  (sys.path mutation above)
    CaptionTrack,
    WaveformDemoScene,
    WaveformFixture,
    capture_camera_frame,
)

from manim_engineering.animation import BeatSpec, SceneCamera  # noqa: E402
from manim_engineering.components import Resistor  # noqa: E402
from manim_engineering.core import CircuitGraph, SignalType  # noqa: E402
from manim_engineering.layout import LayoutEngine  # noqa: E402
from manim_engineering.semantic import LogicLevel, LogicState, Signal  # noqa: E402
from manim_engineering.waveform import derive_bundle_from_signals  # noqa: E402


def _minimal_fixture() -> WaveformFixture:
    """Two-resistor topology with one signal, smallest valid waveform fixture."""
    graph = CircuitGraph()
    r1 = Resistor("a", label="A")
    r2 = Resistor("b", label="B")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    elements = {"a": r1, "b": r2}
    layout = LayoutEngine().layout(graph, elements)

    sig = Signal(name="s", signal_type=SignalType.DIGITAL, value=LogicState(level=LogicLevel.LOW))
    sig.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)
    sig.value = LogicState(level=LogicLevel.HIGH)
    sig.propagate(r1.get_pin("b"), r2.get_pin("a"), graph=graph)

    bundle = derive_bundle_from_signals((sig,))
    return WaveformFixture(
        graph=graph,
        elements=elements,
        layout=layout,
        bundle=bundle,
        signals=(sig,),
    )


def test_waveform_fixture_dataclass_frozen() -> None:
    """A frozen WaveformFixture stops example scenes from mutating between
    ``build_fixture`` and ``teaching_beats`` by accident."""
    fixture = _minimal_fixture()
    assert dataclasses.is_dataclass(fixture)
    fields = {f.name for f in dataclasses.fields(fixture)}
    assert fields == {"graph", "elements", "layout", "bundle", "signals"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        fixture.graph = CircuitGraph()  # type: ignore[misc]


def test_scene_runs_with_minimal_fixture() -> None:
    """A subclass that only implements ``build_fixture`` renders end-to-end."""
    from manim import tempconfig

    class _MinimalDemo(WaveformDemoScene):
        def build_fixture(self) -> WaveformFixture:
            return _minimal_fixture()

    import os
    import tempfile

    os.environ["ME_SUPPRESS_FADE"] = "1"
    try:
        tmpdir = tempfile.mkdtemp(prefix="me_demo_test_")
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": tmpdir,
                "write_to_movie": False,
                "save_last_frame": True,
            }
        ):
            _MinimalDemo().render()
    finally:
        os.environ.pop("ME_SUPPRESS_FADE", None)


def test_capture_camera_frame_writes_png(tmp_path) -> None:
    """``capture_camera_frame`` must drop a non-empty PNG at the requested path."""
    from manim import tempconfig

    captured: dict[str, Path] = {}

    class _SaveDemo(WaveformDemoScene):
        def build_fixture(self) -> WaveformFixture:
            return _minimal_fixture()

        def after_intro_hook(self, _fixture, _camera) -> None:
            target = tmp_path / "intro.png"
            capture_camera_frame(self, target)
            captured["intro"] = target

    import os

    os.environ["ME_SUPPRESS_FADE"] = "1"
    try:
        tmpdir = tmp_path / "manim_media"
        tmpdir.mkdir()
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": str(tmpdir),
                "write_to_movie": False,
                "save_last_frame": True,
            }
        ):
            _SaveDemo().render()
    finally:
        os.environ.pop("ME_SUPPRESS_FADE", None)

    assert captured["intro"].is_file()
    assert captured["intro"].stat().st_size > 0


def test_caption_track_keeps_single_active_mobject() -> None:
    """Drive :class:`CaptionTrack.swap` three times and assert only one
    caption ``Text`` remains uncovered. This regression-guards the closure
    state the original SPI/UART demos kept in a ``caption_box`` dict."""
    from manim import Scene, Text

    fixture = _minimal_fixture()
    sig = fixture.signals[0]
    rec = sig.propagation_history[0]

    scene = Scene()
    seed = Text("seed")
    camera = SceneCamera(frame_width=10.0, frame_height=6.0, frame_cx=0.0, frame_cy=0.0)
    track = CaptionTrack(scene, seed, camera)

    for index, label in enumerate(("first", "second", "third")):
        spec = BeatSpec(signal=sig, record=rec, wave_beat=0, caption=label)
        track.swap(spec, index)

    assert isinstance(track.current, Text)
    assert track.current is not seed

    track.close()
    assert track.current is None


def test_caption_track_ignores_empty_caption() -> None:
    from manim import Scene, Text

    fixture = _minimal_fixture()
    sig = fixture.signals[0]
    rec = sig.propagation_history[0]
    scene = Scene()
    seed = Text("intro")
    camera = SceneCamera(frame_width=10.0, frame_height=6.0, frame_cx=0.0, frame_cy=0.0)
    track = CaptionTrack(scene, seed, camera)

    track.swap(BeatSpec(signal=sig, record=rec, wave_beat=0, caption=""), 0)
    assert track.current is seed
    track.swap(BeatSpec(signal=sig, record=rec, wave_beat=0, caption=None), 1)
    assert track.current is seed


def test_caption_track_removes_previous_mobject() -> None:
    from manim import Scene, Text

    fixture = _minimal_fixture()
    sig = fixture.signals[0]
    rec = sig.propagation_history[0]
    scene = Scene()
    seed = Text("intro")
    scene.add(seed)
    camera = SceneCamera(frame_width=10.0, frame_height=6.0, frame_cx=0.0, frame_cy=0.0)
    track = CaptionTrack(scene, seed, camera)

    track.swap(BeatSpec(signal=sig, record=rec, wave_beat=0, caption="first"), 0)
    assert seed not in scene.mobjects
    assert track.current is not None
    assert track.current is not seed

    prev = track.current
    track.swap(BeatSpec(signal=sig, record=rec, wave_beat=0, caption="second"), 1)
    assert prev not in scene.mobjects
    assert track.current is not None
    assert track.current.text == "second"


def test_hud_scene_uses_default_subtitle_band_when_unspecified() -> None:
    from manim import tempconfig

    seen: dict[str, float] = {}
    real_configure = shared.configure_waveform_scene_camera

    def _capture_camera(scene, layout, panel_spec, bundle, *, subtitle_band=0.0):
        seen["subtitle_band"] = subtitle_band
        return real_configure(
            scene,
            layout,
            panel_spec,
            bundle,
            subtitle_band=subtitle_band,
        )

    class _HudDemo(WaveformDemoScene):
        def build_fixture(self) -> WaveformFixture:
            return _minimal_fixture()

        def hud_texts(self, fixture: WaveformFixture) -> tuple[str, str]:
            return ("Title", "Intro")

    import os
    import tempfile
    from unittest.mock import patch

    os.environ["ME_SUPPRESS_FADE"] = "1"
    try:
        tmpdir = tempfile.mkdtemp(prefix="me_demo_test_")
        with (
            tempconfig(
                {
                    "quality": "low_quality",
                    "disable_caching": True,
                    "media_dir": tmpdir,
                    "write_to_movie": False,
                    "save_last_frame": True,
                }
            ),
            patch.object(shared, "configure_waveform_scene_camera", side_effect=_capture_camera),
        ):
            _HudDemo().render()
    finally:
        os.environ.pop("ME_SUPPRESS_FADE", None)

    assert seen["subtitle_band"] == pytest.approx(shared.DEFAULT_HUD_SUBTITLE_BAND)
