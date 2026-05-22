# Foundation

Engineering visualization framework. Purpose: explain engineering systems through animation.

**Not**: EDA replacement, SPICE simulator, graphics playground, motion experiment.  
**Is**: semantic engineering visualization, teaching-first animation, reusable explanation engine.

## Priorities (strict order)

1. explainability / semantic consistency
2. architecture stability / deterministic behavior
3. API clarity / maintainability
4. educational readability

Optimize understanding over feature count, visual spectacle, or simulation complexity.

## Layer Model

Four dependency layers (lower never depends on upper):

```text
semantic → component → rendering → animation
```

Extended subsystems (owned by semantic or adjacent layers, never bypass semantic):

| Path | Layer | Owns |
|------|-------|------|
| `semantic/` | semantic | topology, signals, buses, state, propagation, timing events |
| `components/` | component | reusable objects, pins, metadata, layout hints |
| `layout/` | component-adjacent | routing, alignment, spacing (no Manim, no animation) |
| `protocol/` | semantic | UART/SPI/I2C/CAN semantics |
| `waveform/` | semantic + render | timing traces derived from signal state |
| `renderers/` | rendering | geometry, symbols, themes, labels |
| `animation/` | animation | motion, highlights, propagation visuals |

**Forbidden dependencies**: semantic→rendering/animation; component→animation; rendering→semantic mutation; animation→topology ownership.

## Layer Contracts

**Semantic** — topology, connectivity, signals, buses, states, propagation, timing. MUST NOT: Manim geometry, rendering, animation, Scene.

**Component** — pins, metadata, semantic behavior, layout hints. MUST inherit `CircuitElement`. MUST NOT: animations, scenes, renderer styles.

**Rendering** — geometry, styling, labels. MUST NOT: mutate topology, own signal state, simulate logic, choreograph scenes.

**Animation** — propagation visuals, highlights, timing emphasis. MUST consume semantic data. MUST NOT: rewrite topology, hidden engineering state, hardcode component internals.

## Repository Layout

```text
src/manim_engineering/
    semantic/
    components/          # passive/, analog/, digital/, common/, measurement/
    layout/
    protocol/
    waveform/
    renderers/           # ieee/, iec/, minimal/, educational/
    animation/           # signal/, focus/, timing/, protocol/

examples/                # basics/, analog/, digital/, protocol/, waveform/
tests/                   # mirrors src structure
experimental/            # must not leak into stable APIs
```

**Forbidden**: `utils.py`, `helpers.py`, `misc.py`, flat giant component dirs, renderer-specific components in `components/`, scene logic in core.

**File size**: prefer one major abstraction per file; avoid >1200 lines without justification.

## Extension Protocol

Before new systems:

1. inspect existing abstractions
2. identify correct layer and owner
3. reuse APIs; no duplicate abstractions
4. minimal architectural impact

Refactors require explicit justification (simplification, deduplication, API stabilization).

## Rule Precedence

On conflict: Foundation → Semantic ownership → Layer boundaries → Domain rules (protocol/waveform/layout) → Renderer → Layout → Animation → Education → Engineering standards → Testing/workflow.
