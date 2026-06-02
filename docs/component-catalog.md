# Component Catalog

Task-driven index of the currently available circuit elements.

Use this when you want to know:

- what components already exist
- which pin names they use
- which example scene demonstrates them

For the low-level contract, see [component-api.md](component-api.md).

## Common / IO

| Component | Import | Typical pins | Example |
|-----------|--------|--------------|---------|
| `InputDriver` | `manim_engineering.components` | `out` | `01_rc_charge.py`, `03_cmos_inverter.py` |
| `VCC` | `manim_engineering.components` | `vcc` | `03_cmos_inverter.py`, `07_zener_regulator.py` |
| `Ground` | `manim_engineering.components` | `gnd` | Most analog examples |

## Passive

| Component | Import | Typical pins | Example |
|-----------|--------|--------------|---------|
| `Resistor` | `manim_engineering.components` | `a`, `b` | `01_rc_charge.py`, `05_opamp_inverting.py` |
| `Capacitor` | `manim_engineering.components` | `a`, `b` | `01_rc_charge.py`, `06_opamp_integrator.py` |
| `Inductor` | `manim_engineering.components` | `a`, `b` | `08_rlc_transient.py` |

## Analog active devices

| Component | Import | Typical pins | Example |
|-----------|--------|--------------|---------|
| `Diode` | `manim_engineering.components` | `anode`, `cathode` | `02_diode_rectifier.py` |
| `ZenerDiode` | `manim_engineering.components` | `anode`, `cathode` | `07_zener_regulator.py` |
| `NMOS` | `manim_engineering.components` | `gate`, `drain`, `source`, `bulk` | `03_cmos_inverter.py`, `09_mos_four_types.py` |
| `PMOS` | `manim_engineering.components` | `gate`, `drain`, `source`, `bulk` | `03_cmos_inverter.py`, `09_mos_four_types.py` |
| `NMOSDepletion` | `manim_engineering.components` | `gate`, `drain`, `source`, `bulk` | `09_mos_four_types.py` |
| `PMOSDepletion` | `manim_engineering.components` | `gate`, `drain`, `source`, `bulk` | `09_mos_four_types.py` |
| `NPN` | `manim_engineering.components` | `base`, `collector`, `emitter` | `04_npn_amplifier.py` |
| `PNP` | `manim_engineering.components` | `base`, `collector`, `emitter` | `09_mos_four_types.py` |
| `OpAmp` | `manim_engineering.components` | `in_p`, `in_n`, `out` | `05_opamp_inverting.py`, `06_opamp_integrator.py` |

## Digital / interface

| Component | Import | Typical pins | Example |
|-----------|--------|--------------|---------|
| `SPIMaster` | `manim_engineering.components` | interface-specific role pins | `examples/protocol/spi_byte_transfer.py` |
| `SPISlave` | `manim_engineering.components` | interface-specific role pins | `examples/protocol/spi_byte_transfer.py` |
| `UARTPort` | `manim_engineering.components` | interface-specific role pins | library only; no standalone demo scene |

## Canonical naming guidance

Prefer these names in new code:

- component accessor: `get_port(...)`
- compatibility alias: `get_pin(...)`
- text override type: `TextPlacementOverride`
- geometry helper: `pin_world_position(...)`

The compatibility aliases remain supported, but this catalog uses the canonical names.

## Choosing an example by task

| Task | Example |
|------|---------|
| Small series chain | `examples/analog/01_rc_charge.py` |
| Diode / rectifier | `examples/analog/02_diode_rectifier.py` |
| CMOS / MOSFET stack | `examples/analog/03_cmos_inverter.py` |
| BJT amplifier | `examples/analog/04_npn_amplifier.py` |
| Op-amp feedback | `examples/analog/05_opamp_inverting.py`, `06_opamp_integrator.py` |
| Regulator / branch node | `examples/analog/07_zener_regulator.py` |
| RLC chain | `examples/analog/08_rlc_transient.py` |
| MOS symbol variants | `examples/analog/09_mos_four_types.py` |
