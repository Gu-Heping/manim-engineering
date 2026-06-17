# Implementation Roadmap

Phased plan for long-running implementation. Each phase completes with **tests + one minimal example** before the next.

**Status**: Phase 8 complete — **layout-track stabilization complete** on `main`. Example library is **analog-first** (`01`–`09`). **3-layer refactor complete** (`core/` graph model, `LayoutEngine.solve`, `MinimalRenderer.render_circuit`, `Port` API with `Pin` aliases). **Phase 7 protocol slice** includes SPI and UART libraries (`protocol/spi/`, `protocol/uart/`); **smoke example retained for SPI only** (`examples/protocol/spi_byte_transfer.py`).

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
- [x] Example path retired into retained smoke `examples/basics/graph_only.py`

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
- [x] Example path retired into analog-first catalog; retained smoke is `examples/basics/graph_only.py`

**Exit criteria**: deterministic structure tests; architecture imports pass.

**Blockers for Phase 5**: none — animation can consume rendered groups via `SignalFlow` without renderer changes.

---

## Phase 5 — Animation primitives (complete)

**Owner**: `animation/`

Deliverables:

- [x] `AnimationPurpose` enum (`propagation` | `timing` | `focus` | `transition`)
- [x] `SignalFlow` consuming semantic propagation metadata + layout wire paths
- [x] `AnimationPrimitive` base + minimal registry
- [x] Local state primitives: `VoltagePulse`, `LogicTransition`
- [x] `tests/animation/` — duration, sequencing, topology guard
- [x] Example teaching scenes now align with analog-first catalog (`examples/analog/01_rc_charge.py`) plus retained protocol smoke (`examples/protocol/spi_byte_transfer.py`); legacy `examples/basics/signal_flow_demo.py` removed

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
- [x] Example waveform scenes now align with analog-first catalog (`examples/analog/01_rc_charge.py`, `examples/analog/03_cmos_inverter.py`); legacy `examples/basics/clock_data_waveform.py` removed

**Exit criteria**: waveform state matches signal state in tests.

**Blockers for Phase 7**: none — protocol FSM can emit `TimingEvent`s and reuse `derive_bundle_from_signals` / `WaveformSync`.

---

## Phase 7 — Protocol vertical slice (complete)

**Owner**: `protocol/` — **SPI + UART**

Deliverables:

- [x] `protocol/spi/` — FSM (`idle` / `active` / `transmitting`), master ownership, mode-0 timing
- [x] `SPIController.transfer_byte` — deterministic `TimingEvent`s + `Signal` updates via `apply_level_between_pins`
- [x] `SPIBusBinding` — graph + clk/mosi/miso/cs; `from_graph_nodes` / `create_bus`; `SPIMaster` / `SPISlave` components
- [x] `protocol/uart/` — FSM (idle / start / data / stop), 8N1 TX timing, `UARTController.transfer_byte`
- [x] `UARTBinding` — graph + tx/rx; covered by `tests/protocol/test_uart_*.py` (no standalone smoke example)
- [x] Waveform via `derive_bundle_from_signals`; SPI example uses `PropagationSequence` + `WaveformSync`
- [x] `tests/protocol/` — FSM, transfer ordering, waveform alignment (SPI + UART)
- [x] Smoke example `examples/protocol/spi_byte_transfer.py` (UART library retained; example deferred during analog-first catalog)

**Exit criteria**: ownership and timing visible; protocol tests deterministic.

**Blockers for Phase 8**: none — extend example READMEs and optional IEC renderer without protocol changes.

---

## Phase 8 — Example library & docs (complete)

Deliverables:

- [x] `examples/` layout established and now converging to analog-first catalog with minimal protocol/basic smoke retained
- [x] Per-directory README (purpose, one-concept table, run commands)
- [x] Master index [examples/README.md](../examples/README.md); root README "Running examples"
- [x] Analog 01–09 scene catalog (`examples/analog/01_rc_charge.py` … `09_mos_four_types.py`)
- [x] Digital logic smoke (`examples/digital/logic_gate_chain.py`)
- [x] Measurement probe smoke (`examples/measurement/probe_chain.py`)
- [x] IEC renderer smoke (`examples/renderers/iec_resistor.py`)
- [x] Minimal protocol/basic smoke retained (`examples/protocol/spi_byte_transfer.py`, `examples/basics/graph_only.py`)
- [x] Renderer variant start (IEC) reuses minimal projection with IEC-facing API/theme,
      rectangular resistor symbol, and IEC-facing MOSFET convention
- [x] Basic digital gates (`ANDGate`, `ORGate`, `NOTGate`) with MinimalRenderer symbols

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

**Steps 1–5 (complete):** deterministic `connection_id`, `scene_bbox` / `MIN_WAVEFORM_GAP`, `SignalFlow` wire ownership, geometry-first regression pipeline.

**Step 6 (complete):**

- [x] AABB wire/waveform overlap guards (`tests/layout/test_geometry_overlap.py`, `layout/aabb.py`)
- [x] Geometry regression guards for layout/waveform spacing and overlap (`tests/layout/test_scene_bbox.py`, `tests/layout/test_geometry_overlap.py`)
- [x] Protocol/layout deterministic geometry contracts (wire replay hash + waveform spacing)
- [x] Rule/doc cross-ref (`90-testing-and-workflow.md` § Visual validation)

**Step 7 (complete):**

- [x] Geometry-only gate retained without raster dHash dependency
- [x] Analog catalog expanded to 01–09 scenes with deterministic layout contracts
- [x] Minimal protocol/basic smoke retained for anti-regression coverage
- [x] Layout stress fixture (`tests/layout/test_layout_stress.py`) — 5-passive chain, occupancy band, wire AABB, replay hash

### Post-governance backlog

- [x] Deterministic `connection_id` on `CircuitGraph.connect()` (sorted port ids)
- [x] Layout guards: `scene_bbox`, `MIN_WAVEFORM_GAP`, waveform `step_polyline` separation
- [x] `SignalFlow` wire ownership regression (`tests/animation/test_signal_flow_ownership.py`)
- [x] Geometry-only merge gates: `test_scene_bbox`, `test_geometry_overlap`, `test_layout_stress`, `test_step_polyline_reveal`
- [x] **Architectural de-duplication (A+B+D)**: topology types collapsed into
      `core/`, scene-level visual tokens lifted to `animation/theme.py`,
      directory maps in rules/docs synced with actual source layout. Guarded
      by `tests/architecture/test_semantic_topology_purity.py` and the
      deleted-shim parametrize in `test_import_layers.py`.
- [x] **arch debt C+E**: pure-topology tests moved out of `tests/semantic/`
      into `tests/core/` (`test_graph_topology.py`, `test_node_pin.py`,
      `test_graph_determinism.py`); examples now converge toward analog-first
      scenes with protocol/basic smoke retained.
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
      OUT pull paths; UART horizontal TX→RX layout. Geometry gates refreshed.

### Stabilization (layout track — complete)

Documentation and CI discipline; topology invariants (`Port.id` contract); post-merge review nits. Does **not** add new protocol features or continuous physics.

- [x] ROADMAP / README / examples index synced with SPI, UART, analog Scope A
- [x] Manim cache + geometry golden update discipline documented
- [x] `Port.id` invariant documented + tested; `Connection.involves` semantics locked
- [x] Animation primitives (`VoltagePulse`, `LogicTransition`) implemented for local state emphasis
- [x] **Layout orientation + upright labels**: `ComponentOrientation`, screen-fixed label slots,
      vertical AUTO side-picking, `text_overrides` / `label_mode_overrides`; presets 03–07 via
      `layout_from_preset`; 07 vertical Rs/Dz; coincident cross-element stub routing in
      `route_nets` (`tests/layout/test_visible_connection.py`)

### Feature backlog (deferred)

Layout preset track is stable on `main`; pick the next feature vertical slice in a dedicated
planning session (Scope B / IEC / I2C — not bundled with stabilization).

IEC renderer symbol expansion beyond resistor/MOS convention; I2C/CAN protocol + geometry goldens; digital gate expansion beyond basic AND/OR/NOT; optional rule 6-file merge; analog **Scope C** (remaining continuous physics beyond RC slice, e.g. RLC damping); measurement examples/meters beyond `VoltageProbe` / `CurrentProbe`; **global netlist auto-placer** (preset-first remains default — see [docs/layout-strategy.md](layout-strategy.md) and `experiments/auto_placer_zener_spike.py`).

**Scope B (RC slice — complete):**

- [x] `RCStepParams` + `derive_rc_waveform_bundle` (`waveform/rc.py`)
- [x] `smooth_polyline` + `polyline_for_trace` dispatch
- [x] `AnalogRamp` animation primitive + beat integration
- [x] `01_rc_charge` upgraded to `WaveformDemoScene` with teaching beats

**Animation orchestration debt (P0+P1 — complete)**

- [x] contract sync (#15)
- [x] protocol / SceneProtocol (#11)
- [x] HUD stage (#10)
- [x] beat merge (#12)
- [x] reveal decouple (#13)
- [x] tests (#14)

**Animation orchestration debt (P2 — complete)**

- [x] panel intro stroke-first (remove `waveform_panel.set_opacity`)
- [x] remove `PropagationSequence.waveform_reveal_callback` bypass
- [x] `WaveformDemoScene` → `animation/teaching_scene.py`
- [x] `CAPTION_CROSSFADE` rule/doc alignment (0.45s, CJK readability)
- [x] primitive `.play()` protocol + E2E smoke (Create assertion, SPI construct)

**Animation observability (P3 — complete)**

- [x] `AnimationTracer` + `ME_ANIMATION_TRACE` / `ME_ANIMATION_TRACE_STDOUT` (`animation/trace.py`)
- [x] Stage wiring: intro, HUD, caption, sequence, beat (`record_stage` checkpoints)
- [x] `BeatAnimationError` with `beat_index` / `signal_name` / `stage` context
- [x] `ME_ANIMATION_SNAPSHOT` beat/intro checkpoints (wraps `debug.snapshot`)
- [x] `TeachingStyle` scene/beat overrides (`animation/style.py`)
- [x] `build_beat_plans` factory + `BeatSpec.timing_mode` (`animation/beat_factory.py`)
- [x] Docs: `animation-timing.md` Debugging, `animation-extensibility.md`, rule 80 Observability + Style

**Intro animation (Tier A — complete)**

- [x] `partition_symbol_strokes` + geometry-aware `play_topology_intro` (`Create` / `DrawBorderThenFill`)
- [x] `IntroStyle` + `WaveformDemoScene.play_intro()` hook
- [x] Trace detail: `line_stroke_count`, `filled_stroke_count`, `use_border_fill`

**Intro animation backlog (Tier B/C complete)**

- [x] Per-symbol / per-layout-order intro factory (`build_intro_plan`)
- [x] Renderer metadata (`element_id` / `connection_id` on mobjects) for semantic wire draw order
- [x] Pin-label `Write` intro mode (opt-in via `pin_label_intro_mode="write"`)

**Animation example migration (complete)**

- [x] `TopologyFixture` + `TopologyTeachingScene` for catalog demos without waveforms
- [x] Analog `02`/`04`–`09` migrated from plain `Scene` + `self.add` to intro/HUD/outro template
- [x] `03_cmos_inverter` upgraded to `WaveformDemoScene` with digital IN/OUT beats
- [x] Construct smoke: `test_analog_topology_scene_smoke.py`, `test_cmos_inverter_scene_smoke.py`

**Animation layer waveform reveal (complete)**

- [x] Idle stub contract: short horizontal segment; `idle_only` default `extend_to_panel=False`
- [x] `baseline_traces` per-signal intro baseline on `WaveformDemoScene`
- [x] Stable segment append (`SegmentRevealPlan`, prefix line preservation, `mount_reveal_plan`)
- [x] `WaveformSegmentController` facade over `WaveformRevealTracker`
- [x] `extend_waveform_to_panel=False` default — opt-in finalize hold to panel edge
- [x] RC 01: vin-only baseline, teach-to-2τ without silent tail

**Animation layer backlog (P4 complete)**

- [x] `beat_factory` tests: `sync` / `ramp` modes and ramp validation errors
- [x] Registry hygiene: stub registration policy + `waveform_sync` registry assertions
- [x] Tier B: `build_intro_plan` per-layout-order intro
- [x] Tier C: renderer mobject metadata for semantic wire draw order
- [x] Scope B/C: implement `VoltagePulse` / `LogicTransition` primitives (replace deferred `build()`)
- [x] Docs: align ROADMAP Phase 5–6 example paths with analog-first catalog (`basics/graph_only`, `protocol/spi_byte_transfer`)

Short-term experiment track: circuitjs1-inspired stamp/doStep exploration is
documented in `docs/circuitjs1-borrowing.md` with an isolated prototype at
`experiments/circuitjs1_stamp_prototype.py` (no runtime coupling).
