# Implementation Roadmap

Phased plan for long-running implementation. Each phase completes with **tests + one minimal example** before the next.

**Status**: Phase 8 complete — example library layout, per-directory READMEs, master index. **3-layer refactor complete** (`core/` graph model, `LayoutEngine.solve`, `MinimalRenderer.render_circuit`, `Port` API with `Pin` aliases). **Phase 7 protocol slice** includes SPI and UART (`protocol/spi/`, `protocol/uart/`). **Analog Scope A** examples: `rc_step_response`, `cmos_inverter`. Next: see **Stabilization** vs **Feature backlog** below.

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
- [x] `protocol/uart/` — FSM (idle / start / data / stop), 8N1 TX timing, `UARTController.transfer_byte`
- [x] `UARTBinding` — graph + tx/rx; example `examples/protocol/uart_byte_transfer.py`
- [x] Waveform via `derive_bundle_from_signals`; examples use `PropagationSequence` + `WaveformSync`
- [x] `tests/protocol/` — FSM, transfer ordering, waveform alignment (SPI + UART)
- [x] Examples `examples/protocol/spi_byte_transfer.py`, `examples/protocol/uart_byte_transfer.py`

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

### Governance execution (Steps 1–6)

**Steps 1–5 (complete):** deterministic `connection_id`, `scene_bbox` / `MIN_WAVEFORM_GAP`, `SignalFlow` wire ownership, visual golden pipeline (dHash + geometry), CI `visual-golden` job.

**Step 6 (complete):**

- [x] AABB wire/waveform overlap guards (`tests/layout/test_geometry_overlap.py`, `layout/aabb.py`)
- [x] SPI dHash golden (`tests/visual/test_spi_byte_transfer_golden.py`)
- [x] Protocol geometry goldens: `spi_byte_transfer`, `uart_byte_transfer` (digest only)
- [x] Rule/doc cross-ref (`90-testing-and-workflow.md` § Visual validation)

**Step 7 (complete):**

- [x] UART dHash golden (`tests/visual/test_uart_byte_transfer_golden.py`, `golden/uart_byte_transfer.dhash.txt`)
- [x] UART geometry golden retained (`tests/visual/test_uart_byte_transfer.py`)
- [x] Minimal analog example (`examples/analog/rc_step_response.py`) + geometry smoke (`tests/visual/test_analog_example_geometry.py`)
- [x] Layout stress fixture (`tests/layout/test_layout_stress.py`) — 5-passive chain, occupancy band, wire AABB, replay hash

### Post-governance backlog

- [x] Deterministic `connection_id` on `CircuitGraph.connect()` (sorted port ids)
- [x] Layout guards: `scene_bbox`, `MIN_WAVEFORM_GAP`, waveform `step_polyline` separation
- [x] `SignalFlow` wire ownership regression (`tests/animation/test_signal_flow_ownership.py`)
- [x] Visual geometry goldens: `acceptance_three_layer`, `spi_byte_transfer`, `uart_byte_transfer`
- [x] **Architectural de-duplication (A+B+D)**: topology types collapsed into
      `core/`, scene-level visual tokens lifted to `animation/theme.py`,
      directory maps in rules/docs synced with actual source layout. Guarded
      by `tests/architecture/test_semantic_topology_purity.py` and the
      deleted-shim parametrize in `test_import_layers.py`.
- [x] **arch debt C+E**: pure-topology tests moved out of `tests/semantic/`
      into `tests/core/` (`test_graph_topology.py`, `test_node_pin.py`,
      `test_graph_determinism.py`); examples `WaveformDemoScene` + helpers in
      `examples/_shared.py` removed ~150 lines of construct boilerplate across
      SPI/UART/clock_data/power_rail. Visual goldens unchanged.
- [x] **Analog symbol set (Scope A)**: `NMOS`, `PMOS`, `Diode`, `OpAmp` as
      `CircuitElement` with `MinimalRenderer` symbols (channel + gate /
      inversion bubble / triangle+bar / op-amp triangle with +/− glyphs);
      `rc_step_response` upgraded to R + NMOS (switch) + C topology; new
      `cmos_inverter` example with two switching beats. Continuous physics
      (RC time constant, MOS threshold, op-amp gain) remains backlog.
- [x] **Teaching example semantics aligned**: progressive waveform reveal
      (`WaveformRevealTracker`, `step_polyline` `max_beat` / `idle_only`);
      `WaveformSync` per-signal isolation; explicit rising/falling edges via
      `record_rising_edge` / `record_falling_edge`; propagation path clip at
      pin anchors; `clock_data` dual nets + four beats; `power_rail_demo` →
      `signal_chain_demo`; RC acceptance (`InputDriver`→R→C→GND); CMOS gate +
      OUT pull paths; UART horizontal TX→RX layout. Visual goldens refreshed.

### Stabilization (current track)

Documentation and CI discipline; topology invariants (`Port.id` contract); post-merge review nits; deferred animation stubs clearly marked. Does **not** add new protocol features or continuous physics.

- [x] ROADMAP / README / examples index synced with SPI, UART, analog Scope A
- [x] Manim cache + geometry golden update discipline documented
- [x] `Port.id` invariant documented + tested; `Connection.involves` semantics locked
- [x] Animation stubs (`VoltagePulse`, `LogicTransition`) marked deferred — not for production scenes

### Feature backlog (deferred)

IEC renderer variant; I2C/CAN protocol + geometry goldens; digital gate `CircuitElement` + render symbols; optional rule 6-file merge; analog **Scope B/C** (continuous physics, RC exponential, `smooth_polyline`, `AnalogRamp` primitive); planned `measurement/` component category.

Short-term experiment track: circuitjs1-inspired stamp/doStep exploration is
documented in `docs/circuitjs1-borrowing.md` with an isolated prototype at
`experiments/circuitjs1_stamp_prototype.py` (no runtime coupling).
