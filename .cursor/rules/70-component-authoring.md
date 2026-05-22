# Component Authoring

Reusable semantic engineering objects in `components/`. Not raw geometry.

## Base Contract

All components MUST inherit `CircuitElement`.

Required surface:

```python
label          # optional
pins           # mandatory for connectable parts
semantic_type
anchor_points
bounds
```

## Pins

Mandatory for connectable components. Expose: ownership, direction, signal type, routing hints, semantic metadata.

**Naming** (lowercase, stable): `gate`, `source`, `drain`, `clk`, `rst`, `vcc`, `gnd`, `tx`, `rx`  
Avoid: `input1`, `magic_pin`, `left_thing`

## Independence

| Forbidden in components | Correct location |
|-------------------------|------------------|
| colors, stroke, renderer conditionals | renderers |
| `animate_*`, `scene.play` | animation / scenes |
| global routing | layout |
| hardcoded renderer geometry | renderers |

## Metadata

Semantic only: voltage domain, logic family, analog role, timing behavior, protocol role.

Categories: `passive`, `analog`, `digital`, `power`, `measurement`, `interface`.

## Granularity

Prefer modular parts (`NMOS`, `ANDGate`, `Mux2to1`) over monoliths (`EntireCPU`, `UniversalChip`).

Complex parts may compose subcomponents internally with semantic structure.

## State

Expose semantic state (logic level, enable, selected channel) explicitly. No hidden animation or renderer state.

## Implementation Order

See `00-foundation.md` § Implementation Order.

## Tests (per component)

Construction, pin existence, bounds, renderer compatibility, layout compatibility.
