# Architecture Reference

Human-readable layer map. Enforced rules: [`.cursor/rules/00-foundation.md`](../.cursor/rules/00-foundation.md).

## Three-layer model (refactor target)

The stable pipeline separates **topology**, **layout**, and **rendering**:

```text
┌─────────────────────────────────────────┐
│  renderers/   Manim adapter only        │
│  ManimRenderer.render(circuit, layout)    │
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
| **Semantic+** | `semantic/`, `protocol/` | signals, propagation, timing (no Manim) |
| **Derived** | `waveform/` | traces derived from signal state (no Manim); drawn in `renderers/` |
| **Motion** | `animation/` | scenes, highlights, `SignalFlow`, `WaveformSync` |

## Target circuit API

```python
from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import ManimRenderer

circuit = CircuitGraph()
r1 = Resistor("R1")
r2 = Resistor("R2")
circuit.add(r1)
circuit.add(r2)
circuit.connect(r1.port_b, r2.port_a)

elements = {"R1": r1, "R2": r2}
layout = LayoutEngine().solve(circuit, elements)
scene = ManimRenderer().render(circuit, layout, elements)
```

`Pin` / `get_pin` / `attach_to` / `render_layout` / `MinimalRenderer` remain as backward-compatible aliases.

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
│  waveform/    timing traces (derived)     │  ← draw in renderers/
└─────────────────────────────────────────┘
```

## Directory map

Subdirectories marked `# planned` are described in the roadmap backlog and
do not yet exist in source.

```text
src/manim_engineering/
    core/                # topology types only (CircuitGraph, Node, Pin, Port, Connection, enums)
    semantic/            # signals, buses, logic states, propagation, timing events
    components/
        passive/         # implemented (Resistor, Capacitor)
        common/          # implemented (Ground, VCC, InputDriver)
        digital/         # implemented (SPIMaster, SPISlave, UARTPort)
        analog/          # implemented (NMOS, PMOS, Diode, OpAmp)
        measurement/     # planned
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
    waveform/            # planned (see basics/clock_data_waveform.py)
tests/
    core/   semantic/   components/   layout/   waveform/   renderers/   protocol/   animation/
    architecture/        # layer guards (no src equivalent)
    visual/              # golden regression (no src equivalent)
```

Topology types (``CircuitGraph``, ``Node``, ``Pin``, ``Port``, ``Connection``,
``PinDirection``, ``PortDirection``, ``ConnectionState``, ``SignalType``,
``TopologyError``) are owned by ``core/`` and not re-exported by ``semantic/``.

Scene-level visual tokens (``DEFAULT_BACKGROUND``, ``BACKGROUND_COLORS``,
``HIGHLIGHT_COLOR``, ``MUTED_COLOR``) are owned by ``animation/theme.py``.
Renderers own renderer-specific semantic colours and stroke widths under
``renderers/<variant>/theme.py``.

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
