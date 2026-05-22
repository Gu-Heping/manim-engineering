# Semantic Core

Engineering meaning before geometry. Model systems, not drawings.

## Core Abstractions

Required renderer-independent types:

- `Signal`, `Pin`, `Node`, `Bus`, `Connection`, `CircuitGraph`, `LogicState`, `TimingEvent`

## Signal

Represents engineering meaning: type, value, direction, timing metadata, propagation state, optional protocol semantics.

MUST expose directionality explicitly:

- `source_pin`, `sink_pin` (or equivalent)
- `direction`: `forward` | `backward` | `bidirectional`

MUST NOT depend on rendering or animation.

## Topology

Connectivity is explicit, not geometry-derived.

```python
graph.connect(a.out, b.in)   # required
```

Forbidden: `if line.intersects(other)`, visual-overlap inference.

## Pin

Semantic interface: ownership, direction, signal type, connection state, routing hints (not visual anchors).

## Bus

First-class grouped topology: synchronized propagation, shared routing — NOT parallel decorative lines.

## State & Timing

State explicit: logic level, voltage, enable, selected path, timing edge.

Timing belongs in semantic layer (delay, edge timing, ordering, synchronization) — not only in animation code.

## Propagation

Propagation defines engineering behavior; animation visualizes it.

```python
signal.propagate(from_pin, to_pin)   # preferred
```

Forbidden: geometry-driven propagation (`if pulse_touches_wire`).

Propagation MUST be deterministic: no random ordering, frame-dependent semantics, or hidden mutation.

State transitions explicit: `LOW→HIGH`, `idle→transmitting`, etc.

## Protocol Semantics (in semantic/)

Model before visuals: ownership, synchronization, framing, arbitration, timing dependency, deterministic state (`idle`, `transmitting`, `waiting_ack`, …).

## Waveform Derivation

Waveforms derive from `Signal` + `TimingEvent` + propagation — not hand-authored fake traces.

## Layer Ownership

| Concern | Owner |
|---------|-------|
| meaning, topology, propagation, timing | semantic |
| symbols, colors, geometry | rendering |
| pulses, highlights, motion | animation |

Animations consume semantics; they do not define them.

```python
SignalFlow(signal)   # correct
signal.animate()     # forbidden
```

## Implementation Order

1. engineering meaning and ownership
2. topology and propagation rules
3. timing and synchronization
4. rendering
5. animation

Never start from raw Manim geometry or pulse effects.
