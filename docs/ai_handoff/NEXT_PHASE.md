# NEXT_PHASE (for AI engineers)

## Focus: polish on stabilized contracts without reopening animation architecture

This phase is not about rebuilding orchestration again. Controller-first reveal
flow, phased beat/sequence execution, and redraw/debug contracts are already in
place. The next phase is about using those stable contracts to improve breadth
and visual polish safely.

## System bottlenecks

## 1) Animation polish now has stable authoring hooks

Current state:
- Tier A/B/C intro work is complete: layout-order intro planning, renderer
  `element_id` / `connection_id` metadata, and opt-in pin-label `Write` mode.
- Local state primitives (`VoltagePulse`, `LogicTransition`) now build real
  `AnimationPlan`s instead of raising deferred errors.

Bottleneck:
- The available hooks need to be applied deliberately in catalog or feature
  slices; ad-hoc scene motion would still bypass the stabilized contracts.

Direction:
- Use `build_intro_plan`, `pin_label_intro_mode`, renderer metadata, and local
  state primitives for visual polish; do not reopen orchestration architecture.

## 2) Protocol/renderer roadmap asymmetry

Current state:
- Protocol layer supports SPI/UART semantics.
- Renderer breadth has started with IEC scaffolding and measurement probe symbols,
  but full IEC symbol parity and additional protocol slices (I2C/CAN) are deferred.

Bottleneck:
- Extending domain breadth risks reopening architecture debt.

Direction:
- New vertical slices must reuse stabilized contracts, not fork orchestration.
- Measurement work beyond `VoltageProbe` / `CurrentProbe` should stay semantic-first;
  do not add visual-only meters or simulator behavior in components/renderers.

## 3) Physics fidelity pressure vs teaching abstraction boundary

Current state:
- RC analog slice is educationally useful, not physically complete.

Bottleneck:
- Contributors may push direct simulator-like features into scene/runtime layers.

Direction:
- Any fidelity increase should start from semantic model contracts, not visual hacks.
