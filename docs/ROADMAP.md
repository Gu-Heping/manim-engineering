# Implementation Roadmap

Phased plan for long-running implementation. Each phase completes with **tests + one minimal example** before the next.

**Status**: Phase 8 complete — example library layout, per-directory READMEs, master index. **3-layer refactor complete** (`core/` graph model, `LayoutEngine.solve`, `MinimalRenderer.render_circuit`, `Port` API with `Pin` aliases). Next: backlog (IEC renderer, analog examples, UART, gate components).

---

## Phase 0 — Scaffold (complete)

- [x] Cursor rules (10 files)
- [x] Docs index, AGENTS, ROADMAP
- [x] `pyproject.toml` / package layout
- [x] `src/manim_engineering/` empty package with layer `__init__.py`
- [x] `tests/architecture/test_import_layers.py` (import direction)
- [x] CI skeleton (pytest, ruff)

**Exit criteria**: `pip install -e .` and `pytest` pass with architecture tests only.

---

## Phase 1 — Semantic core (complete)

**Owner**: `semantic/`

Deliverables:

- [x] `CircuitGraph`, `Node`, `Pin`, `Connection`
- [x] `Signal` with explicit `direction`, `source_pin`, `sink_pin`
- [x] `Bus`, `LogicState`, `TimingEvent`
- [x] Propagation API (`propagate(from_pin, to_pin)`)
- [x] Unit tests; no Manim imports in `semantic/`

**Exit criteria**: topology + propagation tests green; example script builds graph only (no render).

**Blockers for Phase 2**: none — `CircuitElement` can register pins into `CircuitGraph` via `Node`/`Pin` without semantic changes.

---

## Phase 2 — Component base (complete)

**Owner**: `components/`

Deliverables:

- [x] `CircuitElement` base with required surface (`label`, `pins`, `semantic_type`, `anchor_points`, `bounds`)
- [x] `get_pin`, `get_bounds` (defer `render()` to renderer layer)
- [x] Passive stubs: `Resistor`, `Capacitor`, `Ground`, `VCC`
- [x] Pin naming tests

**Exit criteria**: component construction tests; semantic graph connects two pins.

**Blockers for Phase 3**: none — layout can consume `bounds`, `anchor_points`, and pin `routing_hints` without component changes.

---

## Phase 3 — Layout (complete)

**Owner**: `layout/`

Deliverables:

- [x] `layout/types.py` — `Point2D`, `Segment`, `LayoutResult`, occupancy constants
- [x] `layout/grid.py` — deterministic left→right grid placement from bounds
- [x] `layout/routing.py` — orthogonal paths from pin world positions + `routing_hints`
- [x] `layout/engine.py` — `LayoutEngine` places graph nodes and routes connections
- [x] Occupancy heuristic (60–75% on `DEFAULT_NOMINAL_FRAME`; `tests/layout/`)
- [x] Example `examples/basics/layout_two_resistors.py` (no render)

**Exit criteria**: deterministic layout/metric tests; architecture imports pass.

**Blockers for Phase 4**: none — renderer can consume `LayoutResult` pin positions and wire paths.

---

## Phase 4 — Minimal renderer (complete)

**Owner**: `renderers/minimal/`

Deliverables:

- [x] `renderers/minimal/theme.py` — semantic colors per [visual-theme.md](visual-theme.md)
- [x] `MinimalRenderer.render(component)` → Manim `VGroup`
- [x] `MinimalRenderer.render_layout(layout_result, graph, elements)` — wires + placements
- [x] Symbols: Resistor, Capacitor, Ground, VCC (IEEE/IEC deferred)
- [x] `tests/renderers/` — theme + structure tests (`requires_manim` skip when absent)
- [x] Example `examples/basics/render_two_resistors.py`

**Exit criteria**: deterministic structure tests; architecture imports pass.

**Blockers for Phase 5**: none — animation can consume rendered groups via `SignalFlow` without renderer changes.

---

## Phase 5 — Animation primitives (complete)

**Owner**: `animation/`

Deliverables:

- [x] `AnimationPurpose` enum (`propagation` | `timing` | `focus` | `transition`)
- [x] `SignalFlow` consuming semantic propagation metadata + layout wire paths
- [x] `AnimationPrimitive` base + minimal registry
- [x] Stubs: `VoltagePulse`, `LogicTransition` (deferred `build()`)
- [x] `tests/animation/` — duration, sequencing, topology guard
- [x] Example `examples/basics/signal_flow_demo.py`

**Exit criteria**: minimal scene plays propagation; animation tests for sequencing.

**Blockers for Phase 6**: none — waveform can sync to `SignalFlow` / `PropagationRecord` without animation API changes.

---

## Phase 6 — Waveform vertical slice (complete)

**Owners**: `semantic/` + `waveform/` + animation sync

Deliverables:

- [x] `waveform/` — `WaveformTrace`, `WaveformBundle`, derivation from `Signal` / propagation / `TimingEvent`
- [x] `renderers/minimal/waveform.py` — digital step traces aligned below layout
- [x] `WaveformSync` (`AnimationPurpose.TIMING`) — same beat/duration as `SignalFlow`
- [x] `tests/waveform/` — derive, propagate alignment, sync contract
- [x] Example `examples/basics/clock_data_waveform.py`

**Exit criteria**: waveform state matches signal state in tests.

**Blockers for Phase 7**: none — protocol FSM can emit `TimingEvent`s and reuse `derive_bundle_from_signals` / `WaveformSync`.

---

## Phase 7 — Protocol vertical slice (complete)

**Owner**: `protocol/` — **SPI** (UART deferred)

Deliverables:

- [x] `protocol/spi/` — FSM (`idle` / `active` / `transmitting`), master ownership, mode-0 timing
- [x] `SPIController.transfer_byte` — deterministic `TimingEvent`s + `Signal` updates via `apply_level_between_pins`
- [x] `SPIBusBinding` — graph + clk/mosi/miso/cs; `from_graph_nodes` / `create_bus`; `SPIMaster` / `SPISlave` components
- [x] Waveform via `derive_bundle_from_signals`; example uses `SignalFlow` + `WaveformSync`
- [x] `tests/protocol/` — FSM, transfer ordering, waveform alignment
- [x] Example `examples/protocol/spi_byte_transfer.py`

**Exit criteria**: ownership and timing visible; protocol tests deterministic.

**Blockers for Phase 8**: none — extend example READMEs and optional IEC renderer without protocol changes.

---

## Phase 8 — Example library & docs (complete)

Deliverables:

- [x] `examples/` layout: `basics/`, `analog/`, `digital/`, `protocol/`, `waveform/` per `00-foundation.md`
- [x] Per-directory README (purpose, one-concept table, run commands)
- [x] Master index [examples/README.md](../examples/README.md); root README "Running examples"
- [x] `examples/digital/logic_chain.py` — minimal digital propagation smoke
- [x] `examples/waveform/README.md` — points to `basics/clock_data_waveform.py`
- [ ] Renderer variants (IEC) — deferred until minimal renderer stable

**Exit criteria**: all existing examples cataloged; smoke-runnable via `python examples/...`; no layer violations in examples.

---

## Long-task execution notes

### Sizing

| Good task | Bad task |
|-----------|----------|
| Implement `Pin` + tests | Build full SPICE-like simulator |
| SPI semantic FSM | All protocols at once |
| `SignalFlow` for one edge case | Rewrite animation layer |

### Branch / session

- One phase slice or one vertical subsystem per branch
- Update this file: check boxes, note blockers under phase heading

### Definition of done

1. Layer-correct code
2. Unit tests (+ regression if bugfix)
3. Minimal example under `examples/`
4. No new rule violations (see `10-engineering-standards.md`)

### 3-layer refactor (complete)

- [x] `core/` — `CircuitGraph`, `Node`, `Port`, `Connection` (topology only)
- [x] `CircuitGraph.add(element)`, `connect(port_a, port_b)`
- [x] `LayoutEngine.solve` alias; layout stays Manim-free
- [x] `MinimalRenderer.render_circuit(circuit, layout, elements)`
- [x] `Pin` / `get_pin` / `attach_to` backward-compatible aliases
- [x] Architecture import tests include `core/` layer

### Suggested next action

Backlog: IEC renderer variant, `examples/analog/` scenes, UART protocol slice, digital gate `CircuitElement` + render symbols.
