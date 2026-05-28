# ENGINE_CONSTRAINTS (for AI engineers)

## Contracts that should be treated as hard constraints

1. Layer direction from foundation rules.
2. Deterministic IDs and deterministic ordering.
3. Geometry invariants (`scene_bbox`, panel gap, z-order).
4. Scene template orchestration contracts.
5. Tests as behavior contracts, not optional checks.

## Determinism constraints

- `CircuitGraph.connect()` must produce deterministic `connection_id`.
- Layout/routing must avoid random seed dependence.
- Waveform reveal must be beat/time deterministic.
- CI geometry gates must remain stable without raster hacks.

## Ownership constraints

- `core/semantic/protocol/waveform` are Manim-free.
- Renderers do not mutate semantic state.
- Animation does not define topology.
- Components do not own scene choreography.

## Runtime constraints

- `WaveformDemoScene` is the default orchestration template for waveform teaching.
- `TopologyTeachingScene` is for non-waveform catalog scenes.
- Final fade is env-gated (`ME_SUPPRESS_FADE` path must remain supported).

## Validation constraints before accepting major changes

- Keep `tests/architecture/*` green.
- Keep geometry smoke tests green.
- Keep animation sequence tests green.
- Keep example construct smoke tests green.

## Performance constraints

- Prefer simple deterministic algorithms over opaque global optimizers.
- Avoid introducing solver complexity into default layout path.
- Avoid per-frame semantic recomputation in scene loops.

## Backward compatibility constraints

- Legacy aliases remain intentionally (`get_pin`, `render_circuit`, etc.).
- Remove compatibility surface only with explicit migration + tests.

