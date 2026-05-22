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
