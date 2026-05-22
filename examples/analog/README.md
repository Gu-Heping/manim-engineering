# Analog examples

Passive analog-style chains using existing `Resistor` / `Capacitor` stubs — semantic graph and layout only (no SPICE).

## Table

| File | Concept | Key abstractions |
|------|---------|------------------|
| `rc_step_response.py` | R1–C1 chain, layout.solve, one propagate edge | `CircuitGraph`, `Resistor`, `Capacitor`, `LayoutEngine`, `Signal.propagate` |

## Run commands

Smoke (no video):

```bash
python examples/analog/rc_step_response.py
```

Expected output: node/connection counts, occupancy ratio, and per-component placement origins.

## Related

Basics examples (`examples/basics/`) use the same passive symbols for layout and render demos. Protocol and waveform examples add timing panels on top of the same layout engine.
