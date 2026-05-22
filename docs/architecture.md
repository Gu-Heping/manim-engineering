# Architecture Reference

Human-readable layer map. Enforced rules: [`.cursor/rules/00-foundation.md`](../.cursor/rules/00-foundation.md).

## Three-layer model (refactor target)

The stable pipeline separates **topology**, **layout**, and **rendering**:

```text
┌─────────────────────────────────────────┐
│  renderers/   Manim adapter only        │
│  MinimalRenderer.render_circuit(...)    │
├─────────────────────────────────────────┤
│  layout/      placement + routing       │
│  LayoutEngine.solve(circuit, elements)    │
├─────────────────────────────────────────┤
│  core/        CircuitGraph netlist      │
│  components/  pure CircuitElement data  │
└─────────────────────────────────────────┘
```

**Dependency direction** (lower must not import upper):

```text
core → components → layout → renderers → animation
semantic (signals, buses, propagation) extends core; animation consumes semantic
```

| Layer | Package | Owns |
|-------|---------|------|
| **Model** | `core/` | `CircuitGraph`, `Node`, `Port`, `Connection` |
| **Model** | `components/` | `CircuitElement`, footprints, port definitions |
| **Solver** | `layout/` | `LayoutEngine`, placements, wire paths |
| **Adapter** | `renderers/` | Manim `VGroup` projection from layout output |
| **Semantic+** | `semantic/`, `protocol/`, `waveform/` | signals, propagation, timing (no Manim) |
| **Motion** | `animation/` | scenes, highlights, `SignalFlow`, `WaveformSync` |

## Target circuit API

```python
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer

circuit = CircuitGraph()
r1 = Resistor("R1")
r2 = Resistor("R2")
circuit.add(r1)
circuit.add(r2)
circuit.connect(r1.get_port("b"), r2.get_port("a"))

layout = LayoutEngine().solve(circuit, {"R1": r1, "R2": r2})
scene = MinimalRenderer().render_circuit(circuit, layout, {"R1": r1, "R2": r2})
```

`Pin` / `get_pin` / `attach_to` / `render_layout` remain as backward-compatible aliases.

## Extended layer diagram (animation + semantic)

```text
┌─────────────────────────────────────────┐
│  animation/   scenes, motion, focus     │
├─────────────────────────────────────────┤
│  renderers/   geometry, symbols, theme    │
├─────────────────────────────────────────┤
│  components/  CircuitElement, layout hints│
│  layout/      routing, placement          │
├─────────────────────────────────────────┤
│  core/        topology graph              │
│  semantic/    signals, state, propagation │
│  protocol/    bus protocols (semantic)    │
│  waveform/    timing traces (derived)     │
└─────────────────────────────────────────┘
```

## Directory map

```text
src/manim_engineering/
    core/              # graph model only
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
    animation/

examples/
tests/
    core/
    architecture/
```

## Forbidden patterns

| Pattern | Why |
|---------|-----|
| `core` imports Manim or renderers | Model stays pure |
| `semantic` imports Manim | Geometry belongs in renderers |
| `component` owns `scene.play` | Scenes orchestrate |
| `signal.color = ...` | Theme belongs in renderer |
| `NMOS(renderer="ieee")` | Renderer selection external |
| Layout logic inside `renderers/` | Use `LayoutEngine` output |
| Geometry-based connectivity | Topology must be explicit |

## Scenes

Scenes live in `examples/` (or future `scenes/`). They compose primitives; they do not define reusable engineering types.

See [ROADMAP.md](ROADMAP.md) for build order.
