# Timing and Waveform

Waveforms are semantic projections of signal behavior, rendered and animated in upper layers.

## Requirements

- Derive from `Signal`, `TimingEvent`, propagation — no disconnected manual traces
- Stay synchronized with: wire activity, component state, protocol events, animation timing
- Timing modeled semantically before visualization

## Clock & Edges

Clocks: explicit, deterministic, synchronized. Edge concepts (rise/fall, setup/hold, propagation delay) must be visible in timing data, not only in motion aesthetics.

## Visualization (rendering + animation)

- Delayed transitions, edge emphasis, aligned markers, staged propagation
- Avoid simultaneous chaotic updates
- Educational time scaling allowed (exaggerated delay, slowed clocks) when semantic ordering preserved

## Bus Timing

Grouped state changes, synchronization, directionality — buses are not independent unrelated traces.

## Domain Conventions

**Analog traces**: continuous state transitions in semantic model; rendering uses smooth interpolation.

**Digital traces**: discrete states, edge-aligned updates, explicit propagation order.

**Protocol traces**: framing, ACK windows, arbitration — aligned to semantic protocol state machine.

## Layer Ownership

| Layer | Responsibility |
|-------|----------------|
| semantic | timing events, signal state over time |
| waveform/ + renderers | trace layout and drawing |
| animation | synchronized highlights and transitions |

## Determinism

No hidden timing mutation, random event order, or frame-dependent semantic sequencing.
