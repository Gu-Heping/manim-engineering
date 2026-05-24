# Analog Examples

模拟电子教学示例库。每个文件展示一个核心概念。

| 文件 | 概念 | 元件 | 运行命令 |
|------|------|------|----------|
| `01_rc_charge.py` | RC充电回路 | IN, R1, C1, GND | `manim -pql examples/analog/01_rc_charge.py RCChargeScene` |
| `02_diode_rectifier.py` | 半波整流 | AC, D1, RL, GND | `manim -pql examples/analog/02_diode_rectifier.py HalfWaveRectifierScene` |
| `03_cmos_inverter.py` | CMOS反相器 | VCC, P1, N1, IN, GND | `manim -pql examples/analog/03_cmos_inverter.py CMOSInverterScene` |
| `04_npn_amplifier.py` | NPN共发放大器 | VCC, Rc, Q1(NPN), Re, IN, GND | `manim -pql examples/analog/04_npn_amplifier.py NPNAmplifierScene` |
| `05_opamp_inverting.py` | 运放反相放大 | Vin, Rin, Rf, OP, GND | `manim -pql examples/analog/05_opamp_inverting.py OpAmpInvertingScene` |
| `06_opamp_integrator.py` | 运放积分电路 | Vin, Rin, Cf, OP, GND | `manim -pql examples/analog/06_opamp_integrator.py OpAmpIntegratorScene` |
| `07_zener_regulator.py` | 齐纳稳压 | VCC, Rs, Dz, RL, GND | `manim -pql examples/analog/07_zener_regulator.py ZenerRegulatorScene` |
| `08_rlc_transient.py` | RLC暂态响应 | AC, R, L, C, GND | `manim -pql examples/analog/08_rlc_transient.py RLCTransientScene` |

## Fixture smoke contract

Each analog example exposes a `build_*_fixture()` helper so tests can validate
topology/layout deterministically without Manim rendering.
