# CURRENT_STATUS (for AI engineers)

## Project maturity snapshot

- Core/layout/renderer/animation baseline is operational and heavily tested.
- Catalog is analog-first with retained protocol/basic smoke examples plus
  digital gate and measurement probe catalog slices.
- Waveform progressive reveal refactor reached stable-append stage.
- Layout-track stabilization phase is marked complete in roadmap.

## What is implemented now

- Core topology model (`CircuitGraph`, deterministic connections, port contract).
- Semantic propagation and protocol slices (SPI + UART).
- Basic digital gate components (`ANDGate`, `ORGate`, `NOTGate`) with renderer symbols.
- Measurement probes (`VoltageProbe`, `CurrentProbe`) with renderer symbols,
  quickstart build/render coverage, and `examples/measurement/probe_chain.py`.
- Deterministic layout with preset-first strategy and orientation support.
- Minimal renderer with analog/digital symbol coverage and label placement logic.
- Teaching scene templates (waveform + topology variants).
- Beat orchestration with timing/propagation synchronization.
- Observability hooks (`trace`, snapshots) behind env flags.

## Recent animation-layer state (important for handoff)

- Idle trace behavior changed from full-width baseline to short stub contract.
- RC waveform flow now supports:
  - per-trace baseline selection,
  - stable segment append reveal,
  - opt-in finalize-to-panel behavior.
- `WaveformSegmentController` is now the controller-first orchestration path across
  scene, sequence, beat, and beat-factory reveal flows.
- Sequence/beat execution is phased and observable, with static redraw/snapshot/
  inspector contracts aligned on the same displayed-mobject view of the scene.
- Intro planning now has layout-order component stages, renderer semantic
  metadata (`element_id` / `connection_id`), and opt-in pin-label `Write` mode.
- `VoltagePulse` and `LogicTransition` are implemented registered primitives
  for local state emphasis.

## CI/regression posture

- Geometry-first validation replaces raster golden gate dependency.
- Full test suites and geometry smoke are expected blockers.
- Manual video export remains optional inspection tool.

## Catalog status

- Analog scenes (`01`-`09`) are primary.
- Digital gate chain and measurement probe scenes are available as small catalog slices.
- Protocol smoke retained: SPI example.
- UART protocol library exists; standalone demo is deferred.

## Strategic status

- The codebase is in “stabilized architecture + controlled debt burn-down” mode,
  not in greenfield redesign mode.
