# FAILED_EXPERIMENTS (for AI engineers)

## 1) Full-width idle baseline as default waveform intro

What was tried:
- `idle_only` rendered full panel-width horizontal lines.

Why it failed:
- Created false pre-taught waveform context.
- Caused visible discontinuities when beat reveal replaced geometry.

Do not repeat:
- Do not restore full-width idle baseline as default behavior.

## 2) Swap-model reveal (`remove old + insert new`) for beat updates

What was tried:
- Rebuilding full trace segments on each beat and replacing existing lines.

Why it failed:
- Prefix segments disappeared/reappeared.
- Broke continuity and produced “line blink” artifacts.

Do not repeat:
- Avoid full trace replacement when only suffix should advance.

## 3) Pre-add hidden line + Create + post-restore as primary reveal mechanism

What was tried:
- Insert opacity-0 lines before animation and patch visibility afterward.

Why it failed:
- Frame-time semantics diverged from persistent scene state.
- Became patch-heavy and brittle in mixed scenarios.

Do not repeat:
- Do not make pre-add/restore the core reveal model.

## 4) Silent finalize extension to panel edge

What was tried:
- Automatically extending untaught tails after beat sequence end.

Why it failed:
- Introduced non-taught visual content (looked like unexplained state jump).

Do not repeat:
- Keep panel-edge extension explicit and opt-in.

## 5) Scene-wide opacity operations on mixed symbol trees

What was tried:
- Applying bulk opacity resets after intro/focus transitions.

Why it failed:
- Triggered stroke/fill persistence regressions and label artifacts.

Do not repeat:
- Use stroke-aware reveal/restore helpers and focused transforms instead.

## 6) Serial timing playback (flow then waveform) in separate plays

What was tried:
- Independent full-duration plays for propagation and waveform timing.

Why it failed:
- Broke perceived causality and teaching rhythm.

Do not repeat:
- Keep propagation and timing inside one beat group and one run_time.

## 7) Defaulting toward global auto-placer experiments in mainline layout

What was tried:
- Exploring force/opaque global placement ideas for broad topologies.

Why it failed:
- Reduced explainability and deterministic teachable shape control.

Do not repeat:
- Keep auto-placer work isolated in experiments until strict criteria are met.

