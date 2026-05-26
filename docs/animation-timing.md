# Animation Timing Reference

Suggested durations for readable educational pacing. Motion philosophy: [`.cursor/rules/80-animation-and-education.md`](../.cursor/rules/80-animation-and-education.md).

## Duration guidelines

| Category | Seconds | Use |
|----------|---------|-----|
| Small emphasis | 0.3 – 0.6 | pin highlight, edge tick |
| Normal transition | 0.8 – 1.5 | signal step, local reveal |
| Important explanation | 1.5 – 3.0 | propagation across subsystem |
| Comprehension pause | 1.0 – 2.5+ | after major transition (no motion) |

Fast motion only when the concept is already established.

## Animation purpose tag

Each primitive should declare purpose (enforced in API design):

```text
propagation | timing | focus | transition
```

Decorative motion without a tag is disallowed.

## Progressive reveal order

1. global structure  
2. subsystem grouping  
3. active path  
4. local mechanism  
5. timing nuance  
6. edge cases  

## Reusable primitives

```python
from manim_engineering.animation import (
    play_propagation_beat,
    PropagationSequence,
    BEAT_DURATION,
    BEAT_GAP,
    INTRO_PAUSE,
    OUTRO_PAUSE,
)

play_propagation_beat(scene, clk, layout=layout, graph=graph,
    duration=BEAT_DURATION, bundle=bundle, signals=(clk, data),
    panel_spec=panel_spec, beat=0)

PropagationSequence(clk, layout=layout, graph=graph, max_beats=8,
    bundle=bundle, sync_signals=(clk, mosi), panel_spec=panel_spec).play(scene)
```

Legacy per-primitive `SignalFlow(...).play(scene)` then `WaveformSync(...).play(scene)` is discouraged — it serializes motion and breaks sync.

## Waveform sync

When semantic signal state changes, update in the **same beat** (one `scene.play`, one `run_time`):

- propagation pulse along wire copy  
- waveform edge segment flash (`ShowPassingFlash` on trace copy)  
- dependent component state (when modeled)  

### Progressive reveal

Waveform panels in teaching scenes (`WaveformDemoScene` in `examples/_shared.py`)
start with **idle-only** traces (one horizontal segment per signal). Before each
propagation pulse, `WaveformRevealTracker` extends the panel to include the edge
for that beat; `WaveformSync` then flashes that segment while the pulse travels.

Intro must not draw full signal history upfront; that reads as static parallel lines.

### Per-signal flash isolation

`WaveformSync(..., active_signal=beat_signal)` flashes only the trace whose
`signal_name` matches the current beat's signal. Multi-trace scenes (SPI CS/CLK/MOSI,
clock+data) therefore do not cross-flash unrelated lines on CS assert or clk edges.

`play_propagation_beat` passes `active_signal=` automatically from the beat signal.

### Propagation path clipping

`oriented_wire_points` trims routed polylines to the span between pin anchors so
pulses stop at footprint edges and do not interpolate through resistor/capacitor
symbol bodies.

### HUD subtitle-band contract

Scenes that return `hud_texts(...)` should reserve a top band so title/caption do
not overlap topology. `WaveformDemoScene` applies `DEFAULT_HUD_SUBTITLE_BAND`
when `subtitle_band` is unset; protocol demos may override this explicitly.

`CaptionTrack.swap` now ignores empty captions (`None` / `""`) so intro text is
not replaced by an empty `Text` mobject during sparse-caption beat lists.

After each caption `FadeOut`, the previous `Text` is **removed** from the scene
(no parallel crossfade stacking that leaves ghost glyphs).

## Teaching density

At most **2** concepts per scene moment; **1** preferred.

## Educational scaling

Allowed: exaggerated delay, slowed clock, enlarged pulse — semantic ordering must stay correct.

## Pacing constants (`manim_engineering.animation.pacing`)

These are the **single source of truth** for scene pacing. Examples must
import them rather than redefining literals (e.g. ``SPI_BEAT_DURATION``).

| Constant | Default | Use |
|----------|---------|-----|
| `INTRO_PAUSE` | 1.8s | static topology before first beat (after intro fade-in) |
| `BEAT_DURATION` | 1.2s | single propagation + waveform beat |
| `BEAT_GAP` | 0.5s | comprehension pause between beats |
| `BEAT_CAPTION_HOLD` | 0.4s | reading pause after caption FadeIn, before pulse (auto-applied by `PropagationSequence`) |
| `OUTRO_PAUSE` | 1.5s | hold final frame before close |
| `SCENE_FADE_OUT` | 0.8s | length of closing `FadeOut(*self.mobjects)` |
| `OVERLAY_FADE_OUT` | 0.15s | fade before removing propagation/timing overlays each beat |
| `CAPTION_CROSSFADE` | 0.45s | HUD intro → beat caption crossfade |

`SignalFlow`, `WaveformSync`, and `play_propagation_beat` all default to
`BEAT_DURATION`. Pre-2025 code referenced `DEFAULT_PROPAGATION_DURATION` and
`DEFAULT_TIMING_DURATION`; those names now alias `BEAT_DURATION` and exist
only for backwards compatibility.

## Multi-beat protocol scenes

For SPI / UART / clock-data, use `PropagationSequence(beats=...)` with
explicit `BeatSpec` entries so each beat advances the correct semantic
signal and caption. The sequence handles `BEAT_GAP` between beats; pair it
with `subtitle_text(..., role=...)` and a `caption_callback` for HUD swaps.

```python
from manim_engineering.animation import (
    BEAT_GAP,
    BeatSpec,
    PropagationSequence,
    subtitle_text,
)

beats = (
    BeatSpec(signal=binding.cs, record=cs_record, wave_beat=0, caption="① CS↓"),
    BeatSpec(signal=binding.clk, record=clk_history[0], wave_beat=0, caption="② CLK↑ 位 7"),
    # ...
)

PropagationSequence(
    layout=layout,
    graph=graph,
    beats=beats,
    bundle=bundle,
    sync_signals=binding.signals(),
    panel_spec=panel_spec,
    beat_gap=BEAT_GAP,
    caption_callback=swap_caption,
    dim_inactive=True,        # requires topology= (ValueError otherwise)
    topology=topology,
).play(scene)
```

`PropagationSequence` waits `BEAT_CAPTION_HOLD` between every captioned beat's
`caption_callback` invocation and its propagation pulse, so the viewer always
gets time to read the caption before the action starts. Do not also hand-roll
a `self.wait()` between caption and beat — it doubles the gap.

## 3B1B-style entry and exit

Examples (`examples/protocol/*.py`, `examples/basics/*.py`) follow the same
opening / closing template:

```python
from manim import FadeIn, FadeOut
from manim_engineering.animation import (
    INTRO_PAUSE,
    SCENE_FADE_OUT,
    play_topology_intro,
    play_hud_intro,
    scene_final_fade_enabled,
)

# Entry — stroke-first topology reveal (package API; do NOT FadeIn(topology.components)):
play_topology_intro(
    scene,
    topology,
    waveform_panel,
    content,
    components_run_time=0.7,
    wires_run_time=0.5,
    panel_run_time=0.6,
    lag_ratio=0.25,
    total_run_time=1.4,
)
title, intro = play_hud_intro(scene, title_text, intro_text, camera)
self.wait(INTRO_PAUSE - 0.6)

# ... beats ...

# Exit — gated so deterministic geometry/smoke tests keep stable content:
if scene_final_fade_enabled():
    self.wait(max(OUTRO_PAUSE - SCENE_FADE_OUT, 0.2))
    self.play(FadeOut(*self.mobjects, run_time=SCENE_FADE_OUT))
else:
    self.wait(OUTRO_PAUSE)
```

`scene_final_fade_enabled()` returns `False` when the env var
`ME_SUPPRESS_FADE=1` is set (export/preview tooling can set this for
deterministic captures).

## Renderer vs animation (troubleshooting abrupt appear/disappear)

| Symptom | Layer | Typical cause |
|---------|-------|----------------|
| Pin label white halo | Renderer + scene | `FadeIn` / `set_opacity` on a parent of `label_text`; fix with `play_topology_intro` (stroke-first) and `refresh_label_strokes(..., mode="stroke_only")` after dim |
| Resistor zig-zag solid white fill | Animation | `topology.components.set_opacity(1.0)` on mixed VGroup; use `play_topology_intro` + `apply_symbol_opacity` instead |
| Symbol dims but labels stay bright | Animation | `dim_topology` followed by full label refresh; use `stroke_only` during dim |
| Pulse or trace flash vanishes instantly | Animation | Overlay removed after beat; `OVERLAY_FADE_OUT` softens removal |
| Static intro caption disappears at beat 0 | Scene glue | `CaptionTrack.swap` crossfade; tune `CAPTION_CROSSFADE` |
| Wrong symbol shape or wire color | Renderer / layout | Not an animation timing issue |

Static appearance is owned by `MinimalRenderer`; time-axis emphasis is owned by
`PropagationSequence`, `play_propagation_beat`, and `WaveformDemoScene` in
example scene helpers.

## Manim cache (local previews)

Manim caches partial movie segments under `media/videos/<module>/<SceneClass>/partial_movie_files/`.
If you change library code in `src/manim_engineering/` but preview with plain `manim -pql`, you may see **stale frames** from cache even though the package is editable.

**Always do one of the following after editing framework code:**

```bash
# Preferred — bypass cache for this run
manim --disable_caching -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo

# Or delete cached segments for that scene, then re-run
# (path varies by module and Scene class name)
```

Ensure the package is installed editable so Python loads your working tree:

```bash
pip install -e ".[manim]"
```

CI smoke and `scripts/export_example_videos.py` pass `--disable_caching`
(or equivalent `disable_caching` in `tempconfig`) so exported MP4s reflect
current code.

## Debugging (trace + snapshot)

Animation observability is **env-gated** — default CI and renders are unchanged.

| Variable | Behavior |
|----------|----------|
| `ME_ANIMATION_TRACE=1` | Record intro → HUD → sequence → beat stages; flush `media/debug/<SceneName>/trace.json` at scene end |
| `ME_ANIMATION_TRACE_STDOUT=1` | Optional one-line log per stage (requires trace enabled) |
| `ME_ANIMATION_SNAPSHOT=1` | Save PNG + bounds JSON at checkpoints (`01_after_intro`, `beat_NN_before/after`, `99_after_beats`) |

Example:

```bash
ME_ANIMATION_TRACE=1 ME_ANIMATION_SNAPSHOT=1 manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeDemo
```

**Typical triage flow**

1. Re-run with trace on; open `trace.json` and confirm stage order and `beat_index`.
2. If a beat fails, catch `BeatAnimationError` — fields `stage`, `beat_index`, `signal_name`, and `cause` identify the failing beat.
3. With snapshot on, diff `beat_NN_before.png` vs `beat_NN_after.png` for visual regressions.
4. Cross-check pacing overrides via `TeachingStyle` / `BeatSpec.style` before editing primitive code.

See [animation-extensibility.md](animation-extensibility.md) for `TeachingStyle`, `BeatSpec.timing_mode`, and registry extension.
