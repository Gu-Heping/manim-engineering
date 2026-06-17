# Analog Examples

Analog-first teaching examples. Each file demonstrates one core circuit or
symbol concept.

## By task

| Task | Example |
|------|---------|
| Small series chain / RC intro | `01_rc_charge.py` |
| Diode rectifier | `02_diode_rectifier.py` |
| CMOS / MOS gate stack | `03_cmos_inverter.py` |
| BJT amplifier | `04_npn_amplifier.py` |
| Op-amp feedback | `05_opamp_inverting.py`, `06_opamp_integrator.py` |
| Branching regulator topology | `07_zener_regulator.py` |
| RLC chain | `08_rlc_transient.py` |
| MOS symbol variants | `09_mos_four_types.py` |

## Catalog

| File | Concept | Components | Run command |
|------|---------|------------|-------------|
| `01_rc_charge.py` | RC charge path | IN, R1, C1, GND | `manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeScene` |
| `02_diode_rectifier.py` | Half-wave rectifier | AC, D1, RL, GND | `manim --disable_caching -pql examples/analog/02_diode_rectifier.py HalfWaveRectifierScene` |
| `03_cmos_inverter.py` | CMOS inverter | VCC, P1, N1, IN, GND | `manim --disable_caching -pql examples/analog/03_cmos_inverter.py CMOSInverterScene` |
| `04_npn_amplifier.py` | NPN common-emitter amplifier | VCC, Rc, Q1(NPN), Re, IN, GND | `manim --disable_caching -pql examples/analog/04_npn_amplifier.py NPNAmplifierScene` |
| `05_opamp_inverting.py` | Op-amp inverting amplifier | Vin, Rin, Rf, OP, GND | `manim --disable_caching -pql examples/analog/05_opamp_inverting.py OpAmpInvertingScene` |
| `06_opamp_integrator.py` | Op-amp integrator | Vin, Rin, Cf, OP, GND | `manim --disable_caching -pql examples/analog/06_opamp_integrator.py OpAmpIntegratorScene` |
| `07_zener_regulator.py` | Zener regulator | VCC, Rs, Dz, RL, GND | `manim --disable_caching -pql examples/analog/07_zener_regulator.py ZenerRegulatorScene` |
| `08_rlc_transient.py` | RLC transient chain | AC, R, L, C, GND | `manim --disable_caching -pql examples/analog/08_rlc_transient.py RLCTransientScene` |
| `09_mos_four_types.py` | MOSFET symbol variants | NMOS, PMOS, N-DEP, P-DEP | `manim --disable_caching -pql examples/analog/09_mos_four_types.py MosFourTypesScene` |

## Fixture smoke contract

Each analog example exposes a `build_*_fixture()` helper so tests can validate
topology/layout deterministically without Manim rendering.
