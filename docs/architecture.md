# Architecture Reference

Human-readable layer map. Enforced rules: [`.cursor/rules/00-foundation.md`](../.cursor/rules/00-foundation.md).

## Layer diagram

```text
┌─────────────────────────────────────────┐
│  animation/   scenes, motion, focus     │
├─────────────────────────────────────────┤
│  renderers/   geometry, symbols, theme    │
├─────────────────────────────────────────┤
│  components/  CircuitElement, pins        │
│  layout/      routing, placement          │
├─────────────────────────────────────────┤
│  semantic/    topology, signals, state  │
│  protocol/    bus protocols (semantic)    │
│  waveform/    timing traces (derived)     │
└─────────────────────────────────────────┘
```

**Dependency direction** (lower must not import upper):

```text
semantic → component → rendering → animation
```

`layout/`, `protocol/`, `waveform/` sit adjacent to semantic/component; they must not import `animation/` or Manim scenes.

## Directory map (target)

```text
src/manim_engineering/
    semantic/
    components/
        passive/
        analog/
        digital/
        common/
        measurement/
    layout/
    protocol/
    waveform/
    renderers/
        minimal/
        ieee/          # later
        iec/           # later
    animation/
        signal/
        focus/
        timing/
        protocol/

examples/
    basics/
    analog/
    digital/
    protocol/
    waveform/

tests/
    semantic/
    components/
    renderers/
    animation/
    architecture/
```

## Forbidden patterns

| Pattern | Why |
|---------|-----|
| `semantic` imports Manim | Geometry belongs in renderers |
| `component` owns `scene.play` | Scenes orchestrate |
| `signal.color = ...` | Theme belongs in renderer |
| `NMOS(renderer="ieee")` | Renderer selection external |
| Geometry-based connectivity | Topology must be explicit |

## Scenes

Scenes live in `examples/` (or future `scenes/`). They compose primitives; they do not define reusable engineering types.

See [ROADMAP.md](ROADMAP.md) for build order.
