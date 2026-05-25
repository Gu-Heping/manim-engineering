# Animation and Education

Animation explains behavior; scenes orchestrate understanding. Both consume semantic systems.

## Animation Goals

Clarify: causality, propagation direction, timing, state transitions, focus hierarchy.

Every motion MUST map to a purpose: `propagation` | `timing` | `focus` | `transition`.

Forbidden: decorative motion, ambiguous direction, competing simultaneous emphasis.

## Signal Propagation (animation)

Visualize semantic propagation metadata (source→destination). Techniques: traveling highlights, pulses, edge propagation, waveform-linked motion.

Forbidden: visual-only propagation without semantic backing.

### Propagation beat (required API)

- Use `play_propagation_beat` (single beat) or `PropagationSequence(beats=...)` (multi-beat with explicit `BeatSpec`) so **SignalFlow and WaveformSync share one `AnimationGroup` and one `run_time`** on each teaching beat. The sequence handles `BEAT_GAP`, optional `dim_inactive`, and an optional `caption_callback(BeatSpec, index)` for HUD swaps.
- Pulse color **must** come from `theme.color_for_signal_type(signal.signal_type)` — never hard-code a single wire color for all signals.
- Wire `ShowPassingFlash` on renderer paths is opt-in only; default propagation uses detached path copies + semantic-colored pulse.
- Z-order constants live in `manim_engineering.animation.layers` (`TIMING_Z_INDEX=2 < PROPAGATION_Z_INDEX=3 < PULSE_Z_INDEX=4 < HUD_Z_INDEX=10`). Do not redefine.

### HUD subtitles

- Use `subtitle_text(label, role="title|intro|caption")` from `manim_engineering.animation.pacing` for any on-screen text so font (CJK fallback stack), color, and size stay consistent. Position via `hud_text_y(camera.frame_cy, camera.frame_height, row=...)`.
- Caption transitions between beats: `FadeOut(prev) + FadeIn(next)` over ~0.30s — never `ReplacementTransform` on long Chinese strings (the morph is illegible).
- `PropagationSequence` automatically waits `BEAT_CAPTION_HOLD` after every captioned beat's `caption_callback` so the viewer reads the caption before the pulse fires. Do not also hand-roll an extra `self.wait()` between caption and beat — it doubles the gap.

### Camera framing

- All waveform-aware scenes go through `configure_waveform_scene_camera(self, layout, panel_spec, bundle, subtitle_band=...)`. It internally calls `scene_frame_bounds`, `frame_size_for_pixel_aspect`, and `camera_frame_center` in one step and writes only `self.camera.frame_*` (no global `config.frame_*` writes that bleed across scenes). It also applies the 3B1B dark background `#1e1e2e` (override with `apply_background=False` if you need a different colour).

### 3B1B-style scene framing (mandatory for examples)

Per the project animation style brief (see also `docs/animation-timing.md`):

1. **Background**: `configure_waveform_scene_camera` already sets `#1e1e2e`. Never let a scene render on pure black.
2. **Entry**: no bare `self.add(topology, hud)` in the first frame. Call `play_topology_intro(...)` from `manim_engineering.animation` — `Create` on symbol strokes + `FadeIn(waveform_panel)`; hide labels during body reveal, then `show_labels` + `normalize_topology_labels`. **Never** `FadeIn(topology.components)` or `topology.components.set_opacity(1.0)` on mixed groups (activates white fill on Manim `Line` symbols). HUD: `play_hud_intro` uses `FadeIn(title)` (CJK-stable) + `FadeIn(intro, shift=…)`.
3. **Body**: every captioned beat is a crossfade (`FadeOut(prev) + FadeIn(next)`) followed by `BEAT_CAPTION_HOLD` (built into `PropagationSequence`), then the propagation pulse.
4. **Exit**: gate the closing animation with `scene_final_fade_enabled()` so deterministic preview/export runs (which may set `ME_SUPPRESS_FADE=1`) can still capture a content-bearing last frame, but CLI renders end with `self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))`.
5. **Pulse styling**: pulses keep their semantic core colour but wear a warm-gold halo (`theme.HIGHLIGHT_COLOR = "#FFCB6B"`). Never use pure `WHITE` for transient emphasis — too clinical.
6. **`dim_inactive`**: only meaningful with `topology=…` passed in. Passing `dim_inactive=True` without `topology` raises `ValueError` by design; do not catch it.

## Motion Hierarchy

1. active signal  
2. active component  
3. subsystem context  
4. background structure  

Dim inactive systems; isolate active paths.

## Pacing

Rhythm: introduce structure → isolate focus → trigger change → observe propagation → pause.

Include deliberate pauses after major transitions and timing-critical events.

## Progressive Reveal (scenes)

Order: global structure → subsystem grouping → active path → local mechanism → timing nuance → edge cases.

Never expose full complexity at once.

## Teaching Density

**At most 2 concepts per scene moment.** One preferred.

Educational simplification allowed: exaggerated delay, enlarged pulses, simplified symbols — semantic APIs still required.

## Scene Responsibilities (`examples/` / scene scripts)

Orchestrate: pacing, focus order, abstraction transitions.

Must compose reusable primitives (`play_propagation_beat`, `PropagationSequence`, `SignalFlow`, `WaveformSync`, `VoltagePulse`) — no duplicated animation logic or hidden timing hacks. Import pacing from `manim_engineering.animation.pacing` (`INTRO_PAUSE`, `BEAT_DURATION`, `BEAT_GAP`, `OUTRO_PAUSE`) instead of magic numbers.

## Camera

Guide attention, isolate regions, reveal relationships. Forbidden: cinematic drift, constant zoom, dramatic spins.

## Domain Motion

**Analog**: smooth continuous interpolation aligned with semantic state.  
**Digital**: discrete, edge-triggered, synchronized steps.  
**Protocol**: sync, ordering, ownership visible (see `40-protocol-modeling.md`).

## Transitions

Preserve mental continuity (transforms, guided movement). Forbidden: teleportation, unexplained layout jumps.

## Reusable Primitives

Prefer shared animation abstractions over scene-specific hacks.
