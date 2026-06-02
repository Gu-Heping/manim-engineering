# NEXT_PHASE (for AI engineers)

## Focus: polish on stabilized contracts without reopening animation architecture

This phase is not about rebuilding orchestration again. Controller-first reveal
flow, phased beat/sequence execution, and redraw/debug contracts are already in
place. The next phase is about using those stable contracts to improve breadth
and visual polish safely.

## System bottlenecks

## 1) Intro tier backlog still blocks richer teaching pacing

Current state:
- Tier A intro is complete; Tier B/C features (layout-order intro factory,
  renderer metadata-driven draw order, pin-label write mode) remain pending.

Bottleneck:
- Intro extensibility is limited without violating current style contracts.

Direction:
- Implement tiered intro planning without breaking deterministic stage budgets.

## 2) Protocol/renderer roadmap asymmetry

Current state:
- Protocol layer supports SPI/UART semantics, but renderer variants (IEC) and
  additional protocol slices (I2C/CAN) are deferred.

Bottleneck:
- Extending domain breadth risks reopening architecture debt.

Direction:
- New vertical slices must reuse stabilized contracts, not fork orchestration.

## 3) Physics fidelity pressure vs teaching abstraction boundary

Current state:
- RC analog slice is educationally useful, not physically complete.

Bottleneck:
- Contributors may push direct simulator-like features into scene/runtime layers.

Direction:
- Any fidelity increase should start from semantic model contracts, not visual hacks.
