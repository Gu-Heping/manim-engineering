# MOSFET Symbol Reference

Teaching reference for the four **four-terminal** MOSFET types and switchable
MinimalRenderer conventions. Implementation:
[`renderer.py`](../src/manim_engineering/renderers/minimal/renderer.py).

## Default: textbook vertical four-terminal

`MosfetSymbolConvention.textbook_vertical` is the **global default** on
`MinimalRenderer` / `ManimRenderer`.

The enhancement-mode glyph follows the standard **N-channel enhancement**
construction (PMOS mirrors drain/source and bulk-arrow polarity):

1. **Channel** — three **equal discrete vertical bars** at `x = 0.42`, with clear
   gaps (drain / bulk / source thirds). This is **not** a single line with a
   dashed stroke style.
2. **Gate** — solid vertical plate left of the channel (small gap), horizontal
   lead from plate centre to the left (`gate` anchor).
3. **Drain** — from **top** segment centre (NMOS) or **bottom** segment (PMOS):
   horizontal right to `DRAIN_STUB_X`, then vertical to the drain pin.
4. **Bulk (B)** — from **middle** segment centre: horizontal right to
   `SOURCE_STUB_X` with arrow, then vertical to the **source** branch (B–s tie
   on the source stub, adjacent to the source pin — not the drain branch).
5. **Source** — from **bottom** segment centre (NMOS) or **top** segment (PMOS):
   horizontal right to `SOURCE_STUB_X`, then vertical to the source pin.
6. **B–s tie** — bulk stub meets the source branch on `SOURCE_STUB_X` (no symbol
   junction dot; body arrow marks bulk, no bulk pin dot). Gate/drain/source use
   pin dots on all four types.

Drain and source stubs use **different X columns** so stacked CMOS symbols do
not draw overlapping export verticals that short VCC to GND.

Pin anchors (local, 1×1 bounds):

| Pin | NMOS | PMOS |
|-----|------|------|
| gate | (0.0, 0.5) | (0.0, 0.5) |
| drain | (1.0, 1.0) | (1.0, 0.0) |
| source | (0.86, 0.0) | (0.86, 1.0) |
| bulk | (0.86, 0.19) | (0.86, 0.81) |

`bulk` sits at the B–s junction on the source stub column (`SOURCE_STUB_X`).
Scene-level labels (`g`, `d`, `s`, `B`, `T`, formulas) are **not** drawn by the
renderer.

## CMOS inverter preset

[`layout/presets/cmos_inverter.py`](../src/manim_engineering/layout/presets/cmos_inverter.py)
places three electrical nodes:

| Node | Constant | Role |
|------|----------|------|
| Power / ground rail | `RAIL_X = 0.0` | VCC, GND, and MOS source+bulk ties |
| Output | `OUT_X = 0.14` | Shared drain stub column (right of rail) |
| Spine (top → bottom) | `VCC_Y`, `PMOS_DRAIN_Y`, `NMOS_DRAIN_Y`, `GND_Y` | **S–D–D–S** terminal order |

Sources and bulk align to `RAIL_X` (top PMOS source at VCC, bottom NMOS source at
GND). PMOS drain sits above NMOS drain on `OUT_X` so the stack reads S–D–D–S.
`DRAIN_Y` is the midpoint used for OUT label placement.

## Four device types

| Class | Channel | Conduction | Default at Vgs=0 | Teaching note |
|-------|---------|------------|------------------|---------------|
| `NMOS` | N | enhancement | off | Vgs high → on (digital CMOS pull-down) |
| `PMOS` | P | enhancement | off | Vgs low → on (CMOS pull-up) |
| `NMOSDepletion` | N | depletion | on | Solid channel bar (no triple dash) |
| `PMOSDepletion` | P | depletion | on | Complement of N-depletion; bulk arrow outward |

## Legacy conventions (`MosfetSymbolConvention`)

Legacy modes reuse the same anchors and add optional **chevron** decoration on
the source branch for symbol comparison.

| Convention | Extra decoration | Status |
|------------|------------------|--------|
| `textbook_vertical` | Default body above | **default** |
| `ieee_simplified` | Open chevron on source branch | legacy |
| `arrow_on_channel` | Chevron on channel at source branch height | legacy |

## Example

[`examples/analog/09_mos_four_types.py`](../examples/analog/09_mos_four_types.py) —
2×2 grid with bulk tied to source.

## Tests

- [`tests/components/test_analog.py`](../tests/components/test_analog.py)
- [`tests/renderers/test_mosfet_symbols.py`](../tests/renderers/test_mosfet_symbols.py)
- [`tests/layout/test_cmos_inverter_preset.py`](../tests/layout/test_cmos_inverter_preset.py)
- [`tests/layout/test_cmos_no_vertical_short.py`](../tests/layout/test_cmos_no_vertical_short.py)
