# PROJECT_VISION (for AI engineers)

## What this codebase is optimizing

1. Explain engineering causality with deterministic visuals.
2. Keep semantics first, visuals second, animation third.
3. Ship reusable teaching primitives, not one-off scene tricks.

This repository is not trying to maximize visual novelty. It is trying to make
signal behavior legible under strict architectural boundaries.

## What makes it different from plain Manim usage

- Manim is used as a rendering/motion backend, not as the source of truth.
- Engineering truth lives in `core/`, `semantic/`, `protocol/`, `waveform/`.
- Scene code is orchestration only; it must consume semantic state.
- Geometry and animation are required to be replay-stable and testable.

## Non-goals (protect these boundaries)

- Not a SPICE/EDA simulator.
- Not a freeform animation playground.
- Not “draw first, justify later”.
- Not a giant auto-placer project (preset-first layout remains policy).

## Product shape the code is converging to

- **Model plane**: explicit topology + signal/protocol state transitions.
- **Geometry plane**: deterministic placement/routing + waveform panel layout.
- **Visual plane**: minimal renderer conventions + constrained animation language.
- **Teaching plane**: reusable scene templates (`WaveformDemoScene`, `TopologyTeachingScene`).

## Why “AI-first handoff” matters here

Most regressions in this project came from violating layer ownership, not from
missing features. A new AI should prioritize:

1. preserving contracts,
2. extending within the right layer,
3. avoiding visual hacks that bypass semantic truth.

If forced to choose, preserve semantic correctness and determinism over richer
motion effects.

