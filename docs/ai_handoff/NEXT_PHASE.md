# NEXT_PHASE (for AI engineers)

## Focus: remove orchestration ambiguity without destabilizing catalog behavior

This phase is not about adding many new examples. It is about reducing hidden
complexity in the animation orchestration core.

## System bottlenecks

## 1) Reveal orchestration split-brain

Current state:
- Intro baseline logic, beat reveal logic, and finalize logic are managed by
  related but partially separate pathways.

Bottleneck:
- Small visual changes can require touching multiple modules with non-obvious coupling.

Direction:
- Consolidate reveal semantics around segment plans and explicit mount/commit phases.

## 2) Facade not yet first-class in orchestration

Current state:
- `WaveformSegmentController` exists, but orchestration mostly still passes tracker directly.

Bottleneck:
- API intent and implementation reality diverge.

Direction:
- Move sequence/beat orchestration toward controller-centered contracts.

## 3) Intro tier backlog still blocks richer teaching pacing

Current state:
- Tier A intro is complete; Tier B/C features (layout-order intro factory,
  renderer metadata-driven draw order, pin-label write mode) remain pending.

Bottleneck:
- Intro extensibility is limited without violating current style contracts.

Direction:
- Implement tiered intro planning without breaking deterministic stage budgets.

## 4) Protocol/renderer roadmap asymmetry

Current state:
- Protocol layer supports SPI/UART semantics, but renderer variants (IEC) and
  additional protocol slices (I2C/CAN) are deferred.

Bottleneck:
- Extending domain breadth risks reopening architecture debt.

Direction:
- New vertical slices must reuse stabilized contracts, not fork orchestration.

## 5) Physics fidelity pressure vs teaching abstraction boundary

Current state:
- RC analog slice is educationally useful, not physically complete.

Bottleneck:
- Contributors may push direct simulator-like features into scene/runtime layers.

Direction:
- Any fidelity increase should start from semantic model contracts, not visual hacks.

