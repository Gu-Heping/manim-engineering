# PHYSICS_MAPPING (for AI engineers)

## Mapping table (semantic -> visual)

| Semantic concept | Current visual mapping | Owner |
|---|---|---|
| Topology connection | Explicit routed orthogonal path | `layout/` + renderer |
| Digital transition | Step waveform edge + timing flash | `waveform/` + animation |
| Analog transition | Smooth trace segment + optional ramp emphasis | `waveform/` + animation |
| Propagation step | Traveling pulse on overlay path | `animation/signal_flow.py` |
| Signal category | Theme color by signal type | renderer theme |
| Protocol ownership | Beat ordering + active signal flash isolation | protocol + animation |

## What these mappings are not

- They are educational projections, not numerical simulation output.
- They preserve causal ordering, not exact device physics.
- They should never imply unsupported behaviors (e.g., physical current solves).

## Forbidden mappings (do not add)

- “Voltage = brighter line width over time” without semantic field support.
- Inferring current direction from geometric wire orientation alone.
- Random jitter/noise to suggest analog uncertainty.
- Automatic packet sprites for protocol semantics.

## Known physics abstraction boundaries

- RC slice models normalized charge curve for teaching, not full circuit solve.
- MOS/BJT symbols represent topology/polarity semantics, not transistor equations.
- Protocol timing is deterministic FSM/event-driven, not electrical bus analog effects.

## Safe extension strategy

1. Add semantic field/event first.
2. Derive waveform/state from semantic source.
3. Render with existing theme/motion contracts.
4. Validate no contradictory physical implication is introduced.

## Red-flag examples

- Showing a post-beat waveform tail to panel edge when not taught in beats.
- Making traces appear before corresponding semantic beat/time advancement.
- Animating component internals that are not represented in semantic state.

