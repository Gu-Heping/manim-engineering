# ANIMATION_LANGUAGE (for AI engineers)

## Animation grammar in this repo

Every motion must map to one purpose:

- `propagation`
- `timing`
- `focus`
- `transition`

Anything else is visual noise and should be rejected.

## Beat-level contract

Use `play_propagation_beat(...)` or `PropagationSequence(...)`.

Required property: propagation and timing updates share one beat timeline
(single `scene.play` group with same `run_time`), so causality is visible.

## Progressive reveal contract

- Intro does not reveal full trace geometry by default.
- `WaveformRevealTracker` generates `SegmentRevealPlan`.
- Beat mounts new segments then `Create`s them.
- Prefix segments must remain stable (no full trace swap).

## Intro language

- Intro is staged: components -> wires -> panel chrome.
- Strokes are prepared then restored per stage.
- Avoid group-level opacity sweeps on mixed symbol trees.

## Caption/HUD language

- Caption transitions use fade crossfade semantics, not glyph morph tricks.
- Caption read pause is part of sequence contract (`BEAT_CAPTION_HOLD`).
- Subtitle band is a camera/layout concern, not random scene offsets.

## Allowed emphasis tricks

- Time scaling (slower beats, longer pause) if semantic order stays intact.
- Pulse width/color tweaks via style objects.
- Dim inactive topology with reversible focus utilities.

## Disallowed animation patterns

- Separate full-duration `SignalFlow` then `WaveformSync` plays.
- Decorative flashes with no semantic trigger.
- Replacing topology ownership with animation-only states.
- Teleportation between states without transitional causality.

## Practical extension path

When adding new motion:

1. Add/compose a primitive with declared purpose.
2. Integrate via beat factory/plan assembly, not ad-hoc scene callbacks.
3. Add stage/beat tests plus one example usage.

