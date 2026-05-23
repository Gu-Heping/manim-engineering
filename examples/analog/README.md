# Analog examples

Scope A symbol-only models: real analog components (`NMOS`, `PMOS`, `Diode`, `OpAmp`) with deterministic schematic symbols. Semantic graph + layout + digital-edge propagation only — no continuous physics (RC time constant, MOS threshold, op-amp gain). Continuous-physics upgrade is tracked in `docs/ROADMAP.md` (Scope B/C).

## Table

| File | Concept | Key abstractions |
|------|---------|------------------|
| `rc_step_response.py` | R + NMOS (switch) + C + `InputDriver` step | `Resistor`, `NMOS`, `Capacitor`, `InputDriver`, `LayoutEngine.layout(placement_overrides=RC_STEP_OVERRIDES)` |
| `cmos_inverter.py` | CMOS inverter (VCC → PMOS → out ← NMOS → GND; IN gate + OUT pull beats) | `PMOS`, `NMOS`, `record_rising_edge`, `record_falling_edge`, `play_propagation_beat` |

## Run commands

Smoke (no video):

```bash
python examples/analog/rc_step_response.py
python examples/analog/cmos_inverter.py
```

Expected output: node/connection counts, occupancy ratio, per-component placements, and (for the inverter) a one-line summary of each propagation beat.

Render the CMOS inverter (HD):

```bash
python -m manim -qh examples/analog/cmos_inverter.py CMOSInverterDemo
```

## Notes on the digital-edge model

All analog pins use `SignalType.ANALOG`, but `Signal.propagate` still records discrete LOW/HIGH transitions; ANALOG signals do **not** auto-toggle LOW→HIGH the way `DIGITAL`/`CLOCK`/`DATA` do (see `tests/components/test_element.py::test_analog_signal_propagates_through_nmos`). This is the Scope A trade-off: teaching-clear topology and visible switching events over physically continuous traces.

## Related

Basics examples (`examples/basics/`) use the same passive symbols for layout and render demos. Protocol and waveform examples add timing panels on top of the same layout engine. The `WaveformDemoScene` template in `examples/_shared.py` is not used here because there is no waveform panel — the inverter demo runs `play_propagation_beat` directly.

Both analog teaching layouts pin origins manually: `RC_STEP_OVERRIDES` aligns R.b with NMOS.drain at the top edge so routing does not cut through the channel; `INVERTER_OVERRIDES` builds the vertical VCC-PMOS-NMOS-GND stack. The default left-to-right grid is fine for passive chains but not for these symbols.

The CMOS inverter uses `INVERTER_OVERRIDES` because the engine's default grid flattens the canonical vertical stack. The `OUT` net is **not** a graph node — `PMOS.drain` and `NMOS.drain` are connected directly and the scene draws a `Text("OUT")` label at the midpoint. `InputDriver.out` (`semantic_type="io"`) fans out to both gates, replacing the older placeholder-`Resistor` pattern.
