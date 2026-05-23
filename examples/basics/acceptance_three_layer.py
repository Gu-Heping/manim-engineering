"""
Three-layer acceptance: core graph → layout → ManimRenderer + propagation beats.

InputDriver → R1 → C1 → Ground: edge stops at left plate, then right-plate return path.

Preview: ``manim -pql examples/basics/acceptance_three_layer.py AcceptanceScene``
"""

from __future__ import annotations

import sys
from pathlib import Path

_BASICS = Path(__file__).resolve().parent
if str(_BASICS) not in sys.path:
    sys.path.insert(0, str(_BASICS))

from _rc_fixture import build_rc_edge_fixture  # noqa: E402


def build_fixture():
    """Return circuit, elements, layout, signal (two-beat edge history)."""
    circuit, elements, layout, edge, _bundle = build_rc_edge_fixture()
    return circuit, elements, layout, edge


def main() -> None:
    circuit, elements, layout, signal = build_fixture()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(f"edge beats: {len(signal.propagation_history)}")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    _EXAMPLES = Path(__file__).resolve().parents[1]
    if str(_EXAMPLES) not in sys.path:
        sys.path.insert(0, str(_EXAMPLES))

    from _shared import CaptionTrack  # noqa: E402
    from manim_engineering.animation import (
        BEAT_DURATION,
        BeatSpec,
        PropagationSequence,
        configure_topology_scene_camera,
        subtitle_text,
    )
    from manim_engineering.animation import HUD_Z_INDEX
    from manim_engineering.renderers.minimal import ManimRenderer
    from manim_engineering.waveform.layout import hud_text_y

    from manim import FadeIn, Scene

    class AcceptanceScene(Scene):
        """RC edge path with two propagation beats (charge plate + return)."""

        def construct(self) -> None:
            circuit, elements, layout, edge = build_fixture()
            camera = configure_topology_scene_camera(self, layout, subtitle_band=1.0)
            topology = ManimRenderer().render_topology(circuit, layout, elements)
            self.add(topology.circuit_group)
            title = subtitle_text("RC 验收 · Input→R→C→GND", role="title")
            title.set_z_index(HUD_Z_INDEX)
            title.move_to(
                [camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=0), 0.0]
            )
            self.play(FadeIn(title), run_time=0.5)
            self.wait(0.8)
            history = edge.propagation_history
            beats = (
                BeatSpec(
                    signal=edge,
                    record=history[0],
                    wave_beat=0,
                    caption="① 左极板充电路径 (R1→C1.a)",
                ),
                BeatSpec(
                    signal=edge,
                    record=history[1],
                    wave_beat=1,
                    caption="② 右极板回路径 (C1.b→GND)",
                ),
            )
            seed = subtitle_text(
                "Scope A：数字边沿示意（非指数充电曲线）",
                role="intro",
            )
            seed.set_z_index(HUD_Z_INDEX)
            seed.move_to(
                [camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=1), 0.0]
            )
            self.play(FadeIn(seed), run_time=0.4)
            caption_track = CaptionTrack(self, seed, camera)
            PropagationSequence(
                layout=layout,
                graph=circuit,
                beats=beats,
                beat_duration=BEAT_DURATION,
                caption_callback=caption_track.swap,
            ).play(self)
            caption_track.close()
            self.wait(1.5)

except ImportError:
    pass
