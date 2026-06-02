# Animation extensibility

How to customize teaching scenes without forking orchestration code. Timing
defaults live in [animation-timing.md](animation-timing.md); motion philosophy
in [`.cursor/rules/80-animation-and-education.md`](../.cursor/rules/80-animation-and-education.md).

## IntroStyle

Topology reveal before beats uses `IntroStyle` (`manim_engineering.animation.intro_style`):

```python
from manim_engineering.animation import IntroStyle, WaveformDemoScene

class CMOSDemo(WaveformDemoScene):
    intro_style = IntroStyle(
        border_fill_run_time=0.5,
        create_lag_ratio=0.1,
        use_border_fill=True,
    )
```

| Field | Default | Effect |
|-------|---------|--------|
| `border_fill_run_time` | 0.5s | Legacy cap for filled-body timing (stage budget scales via `per_stroke_run_time`) |
| `create_lag_ratio` | 0.1 | Lag between stroke animations within each bulk stage |
| `use_border_fill` | `True` | `False` → all bodies use `Create` (legacy stroke-only intro) |
| `per_stroke_run_time` | 0.10s | Budget per drawable stroke in a stage |
| `min_stage_run_time` | 0.5s | Minimum duration for one intro stage |
| `max_stage_run_time` | 4.0s | Cap for one intro stage |

`play_topology_intro` partitions strokes via `partition_symbol_strokes`: `Line` →
`Create`; filled bodies → `DrawBorderThenFill` when enabled. Stages play
sequentially (components → wires → panel chrome) with per-stage budgets from
`intro_run_time_budget`. Each stage calls `restore_stroke_reveal` after `Create` so
pre-added mobjects stay visible. Waveform trace polylines are excluded by default
(`include_panel_traces=False`); use `play_waveform_idle_baseline` + `restore_waveform_strokes`.

Override `WaveformDemoScene.play_intro()` for per-demo reveal order without
replacing the full `construct()` template.

**Backlog (not Tier A):** per-symbol intro factory (Tier B), semantic wire-path
draw order (Tier C), pin-label `Write` intro mode.

## TeachingStyle

Scene- or beat-level tuning via `TeachingStyle` (`manim_engineering.animation.style`):

```python
from manim_engineering.animation import TeachingStyle, WaveformDemoScene

class RCChargeDemo(WaveformDemoScene):
    style = TeachingStyle(
        beat_duration=1.0,
        beat_gap=0.4,
        dim_opacity=0.45,
        pulse_flash_width=0.6,
    )
```

Per-beat override on `BeatSpec`:

```python
BeatSpec(
    signal=vout,
    record=record,
    caption="强调",
    style=TeachingStyle(beat_duration=2.0),
)
```

Fields: `beat_duration`, `beat_gap`, `caption_crossfade`, `dim_opacity`,
`pulse_flash_width`, `wire_flash_width`, `waveform_flash_width`, `overlay_fade_out`.

Default `TeachingStyle()` matches pacing constants in `animation.pacing` — no
visual change unless you override fields.

`WaveformDemoScene.style.beat_duration` and `beat_gap` are forwarded into the
underlying `PropagationSequence`, so scene-level pacing overrides affect the
actual beat director instead of only local helper code.

## Transition profiles

`BeatSpec.transition_profile` is the preferred beat-authoring entry for motion
layering:

| Value | Behavior |
|-------|----------|
| `default` | Standard beat flow with minimal extra focus staging |
| `setup` | Context-building beat; lighter label/path emphasis before the main play |
| `conclusion` | Result/closure beat; stronger endpoint focus and longer post-hold |

`BeatSpec.emphasis` remains for compatibility and maps into transition profiles.
Prefer `transition_profile` for new scene authoring.

## BeatSpec timing dispatch

`BeatSpec.timing_mode` selects waveform timing for one beat:

| Value | Behavior |
|-------|----------|
| `auto` | `AnalogRamp` when `reveal_time` + analog trace; else `WaveformSync` |
| `sync` | Force `WaveformSync` |
| `ramp` | Force `AnalogRamp` (requires analog trace + `reveal_time`) |
| `none` | Skip waveform timing; propagation/reveal only |

`wire_pulse=False` skips `SignalFlow` while still allowing reveal + timing.

## Beat plan factory

`build_beat_plans()` in `animation/beat_factory.py` is the default hook that
assembles `SignalFlow` + `WaveformSync` / `AnalogRamp` for
`play_propagation_beat`. Custom primitives should:

1. Subclass `AnimationPrimitive` and declare `AnimationPurpose`.
2. Register with `@register_primitive("my_primitive", MyPrimitive)`.
3. Extend or wrap `build_beat_plans` in tests or future factory plugins — do
   **not** embed hidden callables in scene scripts (see rule 80).

Registry introspection:

```python
from manim_engineering.animation import get_primitive, registered_primitives

assert "signal_flow" in registered_primitives()
SignalFlow = get_primitive("signal_flow")
```

## Observability (trace + snapshot)

Environment variables (zero overhead when unset):

| Variable | Effect |
|----------|----------|
| `ME_ANIMATION_TRACE=1` | Write `media/debug/<SceneName>/trace.json` at scene end |
| `ME_ANIMATION_TRACE_STDOUT=1` | One human-readable line per recorded stage |
| `ME_ANIMATION_SNAPSHOT=1` | PNG + bounds JSON at intro / beat / sequence checkpoints |

Typical debug workflow:

```bash
ME_ANIMATION_TRACE=1 ME_ANIMATION_SNAPSHOT=1 manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeDemo
```

1. Open `media/debug/RCChargeDemo/trace.json` — confirm stage order and
   `beat_index` for the failing beat.
2. Compare `beat_NN_before.png` vs `beat_NN_after.png` under the same folder.
3. If a beat raises, read `BeatAnimationError` for `stage`, `beat_index`, and
   `signal_name`; inspect `cause` for the underlying exception.

Stages recorded include `intro.topology`, `hud.intro`, `hud.caption`,
`sequence.beat_start`, `sequence.topology_focus`,
`sequence.topology_focus_settle`, `sequence.caption_settle`,
`sequence.label_focus`, `sequence.label_focus_settle`,
`beat.waveform_commit`, `beat.timing_accent`, `beat.commit_settle`,
`beat.timing_settle`, `beat.play`, `sequence.beat_end`, and
`sequence.post_hold`.

## WaveformDemoScene contract

Subclass `WaveformDemoScene` and implement `build_fixture()`. Optional hooks:

- `teaching_beats(fixture)` → `BeatSpec` tuple
- `hud_texts(fixture)` → `(title, intro)` or `None`
- `style` class attribute → passed to `PropagationSequence` and HUD crossfade
- `intro_style` class attribute → passed to `play_intro()` / `play_topology_intro`
- `propagation_options()` → extra `PropagationSequence` kwargs (`dim_inactive`, etc.)
- `play_intro(topology, waveform_panel, content)` → override for custom reveal order

Additional scene-level contracts:

- `baseline_traces` controls which waveform traces get intro-time idle stubs.
  `sync_idle_baselines(signal_names=...)` snapshots only those selected traces.
- `play_intro_annotations()` is phase-based; it can reveal phase-allowed labels
  beyond `component_label` / `net_label`, including waveform trace labels and
  other role-tagged labels.
- `BeatSpec.record` may be omitted when the signal's propagation history already
  provides the matching record.

`construct()` resets/flushes the tracer automatically when trace env is set.

## TopologyTeachingScene contract

For catalog demos **without** a `WaveformBundle` or propagation beats (most static
analog symbol/layout examples):

```python
from manim_engineering.animation import TopologyFixture, TopologyTeachingScene

class HalfWaveRectifierScene(TopologyTeachingScene):
    subtitle_band = 0.8

    def build_fixture(self) -> TopologyFixture:
        graph, elements, layout = build_rectifier_fixture()
        return TopologyFixture(graph=graph, elements=elements, layout=layout)

    def hud_texts(self, _fixture) -> tuple[str, str]:
        return ("半波整流 · AC→D1→RL→GND", "交流源 → 二极管 → 负载")
```

- Uses `configure_topology_scene_camera` (no waveform panel).
- Default `play_intro()` passes an empty panel `VGroup`; set `intro_panel_run_time = 0.0`.
- Override `render_topology(fixture)` for renderer options (e.g. MOSFET convention).
- Hooks: `after_intro_hook`, `after_hold_hook` (no `PropagationSequence`).

Examples re-export via `examples/_shared.py` for `sys.path` imports.

## What not to do

- Do not call `FadeIn(topology.components)` or `set_opacity` on mixed symbol groups.
- Do not serialise `SignalFlow` then waveform timing/reveal as separate beats or
  separate full-duration plays.
- Do not inject arbitrary Python callbacks into beats — use `BeatSpec` fields and registry.
- Do not import `animation/` from `debug/` (layer direction is one-way).
