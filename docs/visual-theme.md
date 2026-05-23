# Visual Theme Reference

Implementation constants for renderers. Rules: [`.cursor/rules/60-renderer-philosophy.md`](../.cursor/rules/60-renderer-philosophy.md), [`.cursor/rules/10-engineering-standards.md`](../.cursor/rules/10-engineering-standards.md).

Semantic objects do **not** store these values — renderers map `SignalKind` → theme.

## Semantic colors (Manim)

```python
POWER_COLOR   = RED_C
GROUND_COLOR  = GREY_C
CLOCK_COLOR   = YELLOW_C
DATA_COLOR    = GREEN_C
SIGNAL_COLOR  = BLUE_C
ANALOG_COLOR  = TEAL_C
WARNING_COLOR = ORANGE
```

## Backgrounds

Preferred dark engineering backgrounds:

```python
"#1e1e2e"
"#111111"
"#202124"
```

Avoid pure white/black for default scenes.

## Line width hierarchy

```text
major bus       → thick
normal wire     → medium
helper geometry → thin
```

## Typography

Minimal renderer text uses **Manim CE point sizes** (same convention as scene HUD in `animation/pacing.py`), defined in `renderers/minimal/theme.py`:

| Token | Size (pt) | Use |
|-------|-----------|-----|
| Component labels | 20 | R1, P1, VCC, … |
| Waveform trace names | 22 | Timing panel |
| Interface pin names | 18 | SPI/UART pin labels (drawn **outside** the box edge) |
| Interface role glyph | 28 | M / S / U centered inside device box |
| Interface box stroke | 1.25 | Hollow MCU/SLV outline (thinner than passive 3.75) |
| Interface box stroke color | `#9A9AAB` (`GROUND_COLOR`) | Softer than pure white — less halo on colored pin labels |
| Interface panel fill | `#1e1e2e` | Opaque interior behind outline (matches scene background) |

Scene HUD sits above this layer: title 36, caption 26, intro 24.

Interface labels (SPI): `clk`/`mosi`/`cs` on the bus-facing edge; `miso` on the return edge (master right, slave left). MCU/SLV names sit above the highest pin label with bbox clearance.

Waveform trace names often look cleaner than schematic pin names because they sit on uniform dark background with no adjacent box outline — not a separate Text API.

Waveform and interface pin names use `labels.label_text`. Manim `Text` glyphs default to **white stroke** on each path (`stroke_color=#FFFFFF`); `label_text` sets `stroke_color`/`fill_color` to the label color and `stroke_opacity=0` on the whole tree. Pin labels sit `0.26` world units outside the box edge. SPI **miso** is labeled on the master only (slave omits it to avoid overlap in the bus gap); waveform panel still shows `miso`.

## Layout

- Orthogonal routing, 90° turns
- Scene occupancy target: **60%–75%** of frame
- Generous whitespace between subsystems

## Motion (renderer-adjacent)

Renderers produce static geometry. Motion rules live in [animation-timing.md](animation-timing.md).

## Forbidden

- Random per-wire colors
- Rainbow circuits
- Permanent global glow
- Components hardcoding `stroke_color` / `fill_color`

## Renderer modules

```text
renderers/minimal/    # first implementation
renderers/ieee/       # later
renderers/iec/        # later
renderers/educational/  # simplified symbols
```

Centralize theme in each renderer package; share a common `theme.py` when multiple renderers exist.
