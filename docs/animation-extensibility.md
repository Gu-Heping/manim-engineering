# Animation extensibility

How to customize teaching scenes without forking orchestration code. Timing
defaults live in [animation-timing.md](animation-timing.md); motion philosophy
in [`.cursor/rules/80-animation-and-education.md`](../.cursor/rules/80-animation-and-education.md).

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

Stages recorded: `intro.topology`, `hud.intro`, `hud.caption`, `sequence.beat_start`,
`beat.play`, `sequence.beat_end`.

## WaveformDemoScene contract

Subclass `WaveformDemoScene` and implement `build_fixture()`. Optional hooks:

- `teaching_beats(fixture)` → `BeatSpec` tuple
- `hud_texts(fixture)` → `(title, intro)` or `None`
- `style` class attribute → passed to `PropagationSequence` and HUD crossfade
- `propagation_options()` → extra `PropagationSequence` kwargs (`dim_inactive`, etc.)

`construct()` resets/flushes the tracer automatically when trace env is set.

## What not to do

- Do not call `FadeIn(topology.components)` or `set_opacity` on mixed symbol groups.
- Do not serialise `SignalFlow` then `WaveformSync` as separate full-duration plays.
- Do not inject arbitrary Python callbacks into beats — use `BeatSpec` fields and registry.
- Do not import `animation/` from `debug/` (layer direction is one-way).
