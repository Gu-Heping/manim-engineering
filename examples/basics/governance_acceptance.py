"""
Governance acceptance: RC edge layout, waveform band, progressive reveal.

Shares the InputDriver → R1 → C1 → GND topology with ``acceptance_three_layer``.

Preview: ``manim -pql examples/basics/governance_acceptance.py GovernanceAcceptanceScene``
"""

from __future__ import annotations

import sys
from pathlib import Path

_BASICS = Path(__file__).resolve().parent
if str(_BASICS) not in sys.path:
    sys.path.insert(0, str(_BASICS))

from _rc_fixture import build_rc_edge_fixture  # noqa: E402


def build_fixture():
    """Return circuit, elements, layout, edge signal, and waveform bundle."""
    return build_rc_edge_fixture()


def main() -> None:
    circuit, elements, layout, edge, bundle = build_fixture()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(f"scene_bbox height: {layout.scene_bbox.height:.2f}")
    print(f"traces: {[t.signal_name for t in bundle.traces]}")


if __name__ == "__main__":
    main()


try:
    import sys
    from pathlib import Path

    _EXAMPLES = Path(__file__).resolve().parents[1]
    if str(_EXAMPLES) not in sys.path:
        sys.path.insert(0, str(_EXAMPLES))

    from manim import Scene, VGroup
    from PIL import Image

    from manim_engineering.animation import (
        BEAT_DURATION,
        BEAT_GAP,
        INTRO_PAUSE,
        OUTRO_PAUSE,
        BeatSpec,
        PropagationSequence,
        WaveformRevealTracker,
        configure_waveform_scene_camera,
    )
    from manim_engineering.renderers.minimal import ManimRenderer, WaveformPanelRenderer

    _ACCEPTANCE_MEDIA = Path("media/videos/governance_acceptance")

    def _save_camera_frame(scene: Scene, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        frame = scene.camera.get_image()
        if hasattr(frame, "save"):
            frame.save(path)
        else:
            import numpy as np

            Image.fromarray(np.asarray(frame)).save(path)

    class GovernanceAcceptanceScene(Scene):
        """RC edge circuit, waveform panel under wires, two beats + reveal."""

        def construct(self) -> None:
            circuit, elements, layout, edge, bundle = build_fixture()
            topology = ManimRenderer().render_topology(circuit, layout, elements)
            panel_renderer = WaveformPanelRenderer()
            waveform_panel, panel_spec = panel_renderer.render_with_layout(
                bundle, layout, idle_only=True
            )
            reveal = WaveformRevealTracker(waveform_panel, bundle, panel_spec, panel_renderer)
            content = VGroup(topology.components, topology.wires, waveform_panel)
            self.add(content)
            configure_waveform_scene_camera(self, layout, panel_spec, bundle)
            self.wait(0.1)
            _save_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_t0_frame.png")
            self.wait(INTRO_PAUSE)

            history = edge.propagation_history
            beats = (
                BeatSpec(signal=edge, record=history[0], wave_beat=0),
                BeatSpec(signal=edge, record=history[1], wave_beat=1),
            )

            def _reveal(spec: BeatSpec, _index: int) -> None:
                reveal.reveal_for_beat(spec.signal, spec.wave_beat or _index)

            PropagationSequence(
                layout=layout,
                graph=circuit,
                beats=beats,
                bundle=bundle,
                sync_signals=(edge,),
                panel_spec=panel_spec,
                beat_duration=BEAT_DURATION,
                beat_gap=BEAT_GAP,
                waveform_reveal_callback=_reveal,
            ).play(self)
            reveal.reveal_all()
            self.wait(OUTRO_PAUSE)
            _save_camera_frame(self, _ACCEPTANCE_MEDIA / "acceptance_last_frame.png")

except ImportError:
    pass
