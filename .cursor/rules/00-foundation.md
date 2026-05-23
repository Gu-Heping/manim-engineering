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
| `core/` | model | netlist topology only (`CircuitGraph`, ports, connections) — no signals |
| `semantic/` | semantic | signals, buses, state, propagation, timing events (extends core) |
| `waveform/` | semantic-adjacent | derive traces from signal/timing state (no Manim) |
| `renderers/` | rendering | draw symbols, wires, waveform panels from layout + derived traces |
| `animation/` | animation | motion, highlights, propagation visuals |

**Forbidden dependencies**: semantic→rendering/animation; component→animation; rendering→semantic mutation; animation→topology ownership.

## Layer Contracts

**Semantic** — topology, connectivity, signals, buses, states, propagation, timing. MUST NOT: Manim geometry, rendering, animation, Scene.

**Component** — pins, metadata, semantic behavior, layout hints. MUST inherit `CircuitElement`. MUST NOT: animations, scenes, renderer styles.

**Rendering** — geometry, styling, labels. MUST NOT: mutate topology, own signal state, simulate logic, choreograph scenes.

**Animation** — propagation visuals, highlights, timing emphasis. MUST consume semantic data. MUST NOT: rewrite topology, hidden engineering state, hardcode component internals.

## Repository Layout

Subdirectories marked `# planned` are described in the roadmap but do not
yet exist in source — do not import from them.

```text
src/manim_engineering/
    core/                # topology types (CircuitGraph, Node, Pin, Port, Connection, enums)
    semantic/            # signals, buses, logic states, propagation, timing events
    components/
        passive/         # implemented (Resistor, Capacitor)
        common/          # implemented (Ground, VCC, InputDriver)
        digital/         # implemented (SPIMaster, SPISlave, UARTPort)
        analog/          # implemented (NMOS, PMOS, Diode, OpAmp)
        measurement/     # planned (probes, meters)
    layout/
    protocol/            # spi/, uart/ implemented; i2c/, can/ planned
    waveform/
    renderers/
        minimal/         # implemented
        ieee/            # planned
        iec/             # planned
        educational/     # planned
    animation/           # primitives, pacing, scene helpers, theme tokens

examples/
    basics/   analog/   digital/   protocol/
    waveform/            # planned (currently lives in basics/clock_data_waveform.py)
tests/
    core/   semantic/   components/   layout/   waveform/   renderers/   protocol/   animation/
    architecture/        # layer guards (no src equivalent)
    visual/              # golden regression (no src equivalent)
experimental/            # must not leak into stable APIs
```

Topology types (``CircuitGraph``, ``Node``, ``Pin``, ``Port``, ``Connection``,
``PinDirection``, ``PortDirection``, ``ConnectionState``, ``SignalType``,
``TopologyError``) live in ``core/`` and only there. ``semantic/`` consumes
them but must not re-export them.

Scene-level visual tokens (``DEFAULT_BACKGROUND``, ``BACKGROUND_COLORS``,
``HIGHLIGHT_COLOR``, ``MUTED_COLOR``) live in ``animation/theme.py`` and are
shared across renderer variants. Renderers own *semantic* colours
(POWER/GROUND/CLOCK/DATA/…) under ``renderers/<variant>/theme.py``.

**Forbidden**: `utils.py`, `helpers.py`, `misc.py`, flat giant component dirs, renderer-specific components in `components/`, scene logic in core.

**File size**: prefer one major abstraction per file; avoid >1200 lines without justification.

## Extension Protocol

Before new systems:

1. inspect existing abstractions
2. identify correct layer and owner
3. reuse APIs; no duplicate abstractions
4. minimal architectural impact

Refactors require explicit justification (simplification, deduplication, API stabilization).

## Implementation Order

1. semantic definition
2. component definition
3. rendering support
4. animation support
5. tests
6. examples

Never start from raw Manim geometry or decorative motion.

## Rule Precedence

On conflict: Foundation → Semantic ownership → Layer boundaries → Domain rules (protocol/waveform/layout) → Renderer → Layout → Animation → Education → Engineering standards → Testing/workflow.
