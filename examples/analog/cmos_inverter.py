"""
CMOS inverter (Scope A symbol layout).

Topology
--------

.. code::

                    VCC
                     |
                  ===|===
                     |
              IN ----[PMOS]---- (OUT)
                  ===|===
                     |
              IN ----[NMOS]---- (OUT)
                  ===|===
                     |
                    GND

Five nodes (``vcc1``, ``pm1``, ``nm1``, ``gnd1``, ``in_drv``) and five
connections form the canonical CMOS inverter. The input is fanned out by a
single-pin :class:`InputDriver` whose ``out`` port drives both gates; the
``OUT`` net is the direct ``pm1.drain ↔ nm1.drain`` connection, surfaced in
the scene as a ``Text("OUT")`` label rather than a graph node (no placeholder
Resistor pollution).

Layout is **manually pinned** via ``LayoutEngine.layout(..., placement_overrides=)``
to lay out the inverter in its canonical vertical stack (VCC top, GND bottom,
PMOS above NMOS); ``configure_topology_scene_camera`` frames the scene around
the resulting bbox so the diagram is readable at 1080p60.

Smoke: ``python examples/analog/cmos_inverter.py``

Render: ``manim -qh examples/analog/cmos_inverter.py CMOSInverterDemo``
"""

from __future__ import annotations

from manim_engineering.components import VCC, Ground, InputDriver, NMOS, PMOS
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import Point2D
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_falling_edge, record_rising_edge

# Canonical inverter origins (bottom-left corners in world coordinates).
# All five MOSFET/rail right-side pins share x=0.5 so wires form a single
# vertical bus; in_drv sits to the left at the midpoint between the two gates.
INVERTER_OVERRIDES: dict[str, Point2D] = {
    "vcc1":   Point2D(0.3, 3.0),
    "pm1":    Point2D(-0.5, 2.0),
    "nm1":    Point2D(-0.5, 0.2),
    "gnd1":   Point2D(0.3, -0.2),
    "in_drv": Point2D(-3.0, 1.4),
}

# OUT label sits to the right of the drain-drain wire midpoint.
OUT_LABEL_WORLD = (1.1, 1.6)


def build_inverter_fixture():
    """Build the CMOS-inverter graph + manually-placed layout + two beats.

    Returns ``(graph, elements, layout, signals)`` where ``signals`` is a
    dict ``{"in_sig": Signal, "out_sig": Signal}`` whose ``propagation_history``
    holds gate edges on ``in_sig`` and OUT-net pulses on ``out_sig``.
    """
    graph = CircuitGraph()
    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    pmos = PMOS("pm1", label="P1")
    nmos = NMOS("nm1", label="N1")
    in_drv = InputDriver("in_drv", label="IN")

    for comp in (vcc, gnd, pmos, nmos, in_drv):
        comp.attach_to(graph)

    # Power rail: VCC.vcc (OUT, POWER) → PMOS.source (INOUT, ANALOG)
    graph.connect(vcc.get_pin("vcc"), pmos.get_pin("source"))
    # Output net: PMOS.drain (INOUT) ↔ NMOS.drain (INOUT) — no placeholder.
    graph.connect(pmos.get_pin("drain"), nmos.get_pin("drain"))
    # Ground rail: NMOS.source (INOUT) → GND.gnd (IN, GROUND)
    graph.connect(nmos.get_pin("source"), gnd.get_pin("gnd"))
    # Input fanout: in_drv.out (OUT, ANALOG) → PMOS.gate + NMOS.gate.
    graph.connect(in_drv.get_pin("out"), pmos.get_pin("gate"))
    graph.connect(in_drv.get_pin("out"), nmos.get_pin("gate"))

    elements = {
        "vcc1": vcc,
        "gnd1": gnd,
        "pm1": pmos,
        "nm1": nmos,
        "in_drv": in_drv,
    }
    layout = LayoutEngine().layout(
        graph,
        elements,
        placement_overrides=INVERTER_OVERRIDES,
    )

    in_sig = Signal(
        name="IN",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    out_sig = Signal(
        name="OUT",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.HIGH),
    )
    record_rising_edge(in_sig, in_drv.get_pin("out"), nmos.get_pin("gate"), graph=graph)
    record_rising_edge(out_sig, pmos.get_pin("drain"), nmos.get_pin("drain"), graph=graph)
    record_falling_edge(in_sig, in_drv.get_pin("out"), pmos.get_pin("gate"), graph=graph)
    record_falling_edge(out_sig, pmos.get_pin("drain"), nmos.get_pin("drain"), graph=graph)

    return graph, elements, layout, {"in_sig": in_sig, "out_sig": out_sig}


def main() -> None:
    graph, _elements, layout, signals = build_inverter_fixture()
    print(f"nodes: {len(graph.nodes)}, connections: {len(graph.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    print(
        "scene_bbox: "
        f"x[{layout.scene_bbox.min_x:.2f},{layout.scene_bbox.max_x:.2f}] "
        f"y[{layout.scene_bbox.min_y:.2f},{layout.scene_bbox.max_y:.2f}]"
    )
    for placement in layout.placements:
        print(
            f"{placement.element_id}: "
            f"origin=({placement.origin.x:.3f}, {placement.origin.y:.3f})"
        )
    for label, sig in signals.items():
        last = sig.propagation_history[-1]
        print(f"{label}: {last.from_pin_id} → {last.to_pin_id} ({last.state_transition})")


if __name__ == "__main__":
    main()


try:
    from manim import DOWN, UP, FadeIn, FadeOut, LaggedStart, Scene, Text, VGroup

    from manim_engineering.animation import (
        BEAT_GAP,
        HUD_Z_INDEX,
        INTRO_PAUSE,
        OUTRO_PAUSE,
        SCENE_FADE_OUT,
        configure_topology_scene_camera,
        play_propagation_beat,
        scene_final_fade_enabled,
        subtitle_text,
    )
    from manim_engineering.renderers.minimal import ManimRenderer
    from manim_engineering.renderers.minimal import theme as renderer_theme
    from manim_engineering.waveform.layout import hud_text_y

    class CMOSInverterDemo(Scene):
        """CMOS inverter teaching demo (no waveform panel).

        Vertical canonical layout (VCC top, GND bottom, PMOS above NMOS) plus
        a left-side ``IN`` driver and an explicit ``OUT`` text label at the
        drain-drain midpoint. Two beats:

        1. Input rises → NMOS conducts → OUT pulled to GND.
        2. Input falls → PMOS conducts → OUT pulled to VCC.

        Camera framing comes from :func:`configure_topology_scene_camera`
        (topology-only; no waveform panel), so the inverter occupies the
        majority of the viewport rather than being squashed by Manim's
        default 14.2×8 frame.
        """

        def construct(self) -> None:
            graph, elements, layout, signals = build_inverter_fixture()
            # ``configure_topology_scene_camera`` shifts the camera up by
            # subtitle_band/2 so HUD captions reserve a top band; the title
            # must be anchored to the resulting frame top (not Manim's default
            # world-origin frame). ``hud_text_y`` gives the correct world y
            # given the actual camera params, regardless of frame offset.
            camera = configure_topology_scene_camera(self, layout, subtitle_band=1.2)

            topology = ManimRenderer().render_topology(graph, layout, elements)
            out_label = Text(
                "OUT",
                font_size=renderer_theme.COMPONENT_LABEL_FONT_SIZE,
                color=renderer_theme.component_stroke_color(),
            )
            out_label.move_to([OUT_LABEL_WORLD[0], OUT_LABEL_WORLD[1], 0.0])
            content = VGroup(topology.components, topology.wires, out_label)
            self.add(content)

            title = subtitle_text("CMOS Inverter · 输入翻转输出", role="title")
            title.set_z_index(HUD_Z_INDEX)
            title.move_to(
                [camera.frame_cx, hud_text_y(camera.frame_cy, camera.frame_height, row=0), 0.0]
            )

            self.play(
                LaggedStart(
                    FadeIn(topology.components, shift=0.15, run_time=0.7),
                    FadeIn(topology.wires, run_time=0.5),
                    FadeIn(out_label, run_time=0.4),
                    lag_ratio=0.25,
                ),
                run_time=1.3,
            )
            self.play(FadeIn(title, shift=0.08), run_time=0.5)
            self.wait(max(INTRO_PAUSE - 0.6, 0.3))

            caption_high = subtitle_text(
                "① 输入↑ → NMOS 导通 → 输出拉到 GND",
                role="caption",
            )
            caption_high.set_z_index(HUD_Z_INDEX)
            caption_high.next_to(title, DOWN, buff=0.25)

            caption_low = subtitle_text(
                "② 输入↓ → PMOS 导通 → 输出拉到 VCC",
                role="caption",
            )
            caption_low.set_z_index(HUD_Z_INDEX)
            caption_low.next_to(title, DOWN, buff=0.25)

            self.play(FadeIn(caption_high), run_time=0.4)
            play_propagation_beat(
                self,
                signals["in_sig"],
                layout=layout,
                graph=graph,
                record=signals["in_sig"].propagation_history[0],
            )
            play_propagation_beat(
                self,
                signals["out_sig"],
                layout=layout,
                graph=graph,
                record=signals["out_sig"].propagation_history[0],
            )
            self.wait(BEAT_GAP)

            self.play(FadeOut(caption_high, run_time=0.3), FadeIn(caption_low, run_time=0.3))
            play_propagation_beat(
                self,
                signals["in_sig"],
                layout=layout,
                graph=graph,
                record=signals["in_sig"].propagation_history[1],
            )
            play_propagation_beat(
                self,
                signals["out_sig"],
                layout=layout,
                graph=graph,
                record=signals["out_sig"].propagation_history[1],
            )
            self.wait(BEAT_GAP)

            self.play(FadeOut(caption_low, run_time=0.3))
            if scene_final_fade_enabled():
                self.wait(max(OUTRO_PAUSE - SCENE_FADE_OUT, 0.2))
                self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))
            else:
                self.wait(OUTRO_PAUSE)

except ImportError:
    pass
