# Animation and Education

Animation explains behavior; scenes orchestrate understanding. Both consume semantic systems.

## Animation Goals

Clarify: causality, propagation direction, timing, state transitions, focus hierarchy.

Every motion MUST map to a purpose: `propagation` | `timing` | `focus` | `transition`.

Forbidden: decorative motion, ambiguous direction, competing simultaneous emphasis.

## Signal Propagation (animation)

Visualize semantic propagation metadata (source-to-destination). Techniques: traveling highlights, pulses, edge propagation, waveform-linked motion.

Forbidden: visual-only propagation without semantic backing.

### Propagation beat (required API)

- Use `play_propagation_beat` (single beat) or `PropagationSequence(beats=...)` (multi-beat with explicit `BeatSpec`) so each teaching beat preserves **causal sync** between propagation, waveform reveal/timing, and any dependent component emphasis.
- The implementation may be phased (`topology_focus`, label/caption settles, commit/timing/playback), but it must not split one semantic beat into multiple unrelated beats.
- Pulse color **must** come from `theme.color_for_signal_type(signal.signal_type)`; never hard-code a single wire color for all signals.
- Wire `ShowPassingFlash` on renderer paths is opt-in only; default propagation uses detached path copies plus semantic-colored pulse.
- Z-order constants live in `manim_engineering.animation.layers` (`TIMING_Z_INDEX=2 < PROPAGATION_Z_INDEX=3 < PULSE_Z_INDEX=4 < HUD_Z_INDEX=10`). Do not redefine.

### HUD subtitles

- Use `subtitle_text(label, role="title|intro|caption")` from `manim_engineering.animation.pacing` for any on-screen text so font, color, and size stay consistent. Position via `hud_text_y(camera.frame_cy, camera.frame_height, row=...)`.
- Caption transitions between beats: `FadeOut(prev) + FadeIn(next)` over about `CAPTION_CROSSFADE`; never `ReplacementTransform` long text strings.
- `PropagationSequence` automatically waits `BEAT_CAPTION_HOLD` after every captioned beat's `caption_callback` so the viewer reads the caption before the pulse fires. Do not hand-roll an extra `self.wait()` between caption and beat.

### Camera framing

- All waveform-aware scenes go through `configure_waveform_scene_camera(self, layout, panel_spec, bundle, subtitle_band=...)`. It writes only `self.camera.frame_*` and applies the default dark background `#1e1e2e` unless explicitly overridden.

### 3B1B-style scene framing (mandatory for examples)

Per the project animation style brief (see also `docs/animation-timing.md`):

1. **Background**: `configure_waveform_scene_camera` already sets `#1e1e2e`. Never let a scene render on pure black.
2. **Entry**: no bare `self.add(topology, hud)` in the first frame. Call `play_topology_intro(...)` (or override `WaveformDemoScene.play_intro()`). Use `Create` on `Line` symbol strokes and `DrawBorderThenFill` on filled bodies when `IntroStyle.use_border_fill` is enabled. For per-symbol entry, use `build_intro_plan(..., component_order="layout")`; do not hand-roll component sequencing in examples. Renderer topology mobjects expose `element_id` / `connection_id` metadata for semantic ordering.
3. **Label lifecycle**: labels are phase-driven. Hide them during intro body reveal, then let `play_intro_annotations()` reveal only phase-allowed roles. Interface pin labels may opt into `pin_label_intro_mode="write"`; default catalog behavior remains fade. Never `FadeIn(topology.components)` or call `topology.components.set_opacity(1.0)` on mixed groups.
4. **Body**: every captioned beat is a crossfade (`FadeOut(prev) + FadeIn(next)`) followed by the sequence's built-in pre-beat settles (`topology_focus`, caption/label settles when applicable), then the main beat playback.
5. **Exit**: gate the closing animation with `scene_final_fade_enabled()` so deterministic preview/export runs can still capture a content-bearing last frame, but normal renders end with `FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT)`.
6. **Pulse styling**: pulses keep their semantic core color but wear a warm-gold halo (`theme.HIGHLIGHT_COLOR = "#FFCB6B"`). Never use pure white for transient emphasis.
7. **`dim_inactive`**: only meaningful with `topology=` passed in. Passing `dim_inactive=True` without `topology` raises `ValueError` by design; do not catch it.

## Motion Hierarchy

1. active signal
2. active component
3. subsystem context
4. background structure

Dim inactive systems; isolate active paths.

## Pacing

Rhythm: introduce structure -> isolate focus -> trigger change -> observe propagation -> pause.

Include deliberate pauses after major transitions and timing-critical events.

## Progressive Reveal (scenes)

Order: global structure -> subsystem grouping -> active path -> local mechanism -> timing nuance -> edge cases.

Never expose full complexity at once.

## Teaching Density

**At most 2 concepts per scene moment.** One preferred.

Educational simplification allowed: exaggerated delay, enlarged pulses, simplified symbols; semantic APIs still required.

## Scene Responsibilities (`examples/` / scene scripts)

Orchestrate: pacing, focus order, abstraction transitions.

Must compose reusable primitives (`play_propagation_beat`, `PropagationSequence`, `SignalFlow`, `WaveformSync`, `VoltagePulse`) with pacing from `manim_engineering.animation.pacing`. No duplicated animation logic or hidden timing hacks.

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

## Observability

- Trace and snapshot are **env-gated** (`ME_ANIMATION_TRACE`, `ME_ANIMATION_SNAPSHOT`). Default renders and CI must not depend on them.
- Use `record_stage` checkpoints for machine-readable timelines. Sequence/beat tracing should reflect the current phased director (`sequence.topology_focus`, `sequence.caption_settle`, `sequence.label_focus`, `beat.waveform_commit`, `beat.timing_accent`, `beat.play`, etc.), not only coarse intro/beat markers.
- Beat failures must surface as `BeatAnimationError` with `beat_index`, `signal_name`, and `stage`; do not swallow exceptions inside sequence loops.
- Full env table and triage flow: [docs/animation-timing.md](../docs/animation-timing.md#debugging-trace--snapshot) and [docs/animation-extensibility.md](../docs/animation-extensibility.md).

## Style overrides

- Scene defaults: `WaveformDemoScene.style = TeachingStyle(...)`.
- Beat overrides: `BeatSpec.style` or `BeatSpec.duration` (duration merges into resolved style).
- Prefer `BeatSpec.transition_profile` for beat-level motion semantics; `emphasis` remains a compatibility mapping, not the primary authoring surface.
- Timing dispatch: `BeatSpec.timing_mode` (`auto` | `sync` | `ramp` | `none`). Do not fork `play_propagation_beat` for per-beat waveform choice.
- Extend beats via `build_beat_plans` plus registry primitives; forbidden: arbitrary callables in scene scripts.
