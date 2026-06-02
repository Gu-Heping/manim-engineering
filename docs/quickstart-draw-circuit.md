# Quickstart: Draw a Circuit

Task-first path for users or agents who want a circuit diagram without first
learning every internal layer.

If you need architecture details later, see [architecture.md](architecture.md).
If you only want to get a diagram on screen, start here.

## The shortest path

The task-level API now has three stages:

1. `build_circuit(...)` — register elements and connect pins
2. `layout_circuit(...)` — run deterministic layout and collect warnings
3. `render_circuit_diagram(...)` — project the result to Manim geometry

```python
from manim_engineering import (
    build_circuit,
    layout_circuit,
    render_circuit_diagram,
)
from manim_engineering.components import Ground, InputDriver, Resistor
from manim_engineering.core import SignalType

build = build_circuit(
    {
        "vin": InputDriver("vin", label="IN", signal_type=SignalType.ANALOG),
        "r1": Resistor("r1", label="R1"),
        "gnd": Ground("gnd", label="GND"),
    },
    [
        ("vin", "out", "r1", "a"),
        ("r1", "b", "gnd", "gnd"),
    ],
)

layout = layout_circuit(build)
diagram = render_circuit_diagram(build, layout)

topology_group = diagram.rendered
warnings = layout.warnings
```

These helpers are available from the top-level package, alongside common
components and layout/rendering primitives such as `Resistor`, `Ground`,
`LayoutEngine`, and `ManimRenderer`.

## What each stage gives you

### `build_circuit(...)`

Use this instead of manually doing:

- `CircuitGraph()`
- `element.attach_to(graph)` for each component
- `graph.connect(...)` with live port objects

Input format:

- `elements`: `{"id": component}` or `[("id", component), ...]`
- `connections`: `(from_element_id, from_pin, to_element_id, to_pin)`

This is the recommended path for agents because it avoids pin-object plumbing.

### `layout_circuit(...)`

This wraps the current deterministic layout path and gives you diagnostics.

Return fields:

- `layout`: the underlying `LayoutResult`
- `layout_mode`: currently `semantic_grid`, `structured_auto`, or `manual`
- `warnings`: machine-readable warning strings
- `needs_attention`: `True` when the diagram likely needs preset/manual help

Current warning examples:

- `layout.occupancy_above_target`
- `layout.single_row_auto_grid`
- `layout.branching_topology_using_auto_grid` (when forcing plain auto-grid on branching topologies)

If `needs_attention` is true, do not assume the rendered circuit is acceptable
just because rendering succeeded.

## When auto layout is enough

The current automatic path is best for:

- small left-to-right chains
- simple RC / rectifier / series passive examples
- quick topology smoke checks

It is **not** strong enough for many textbook schematics by itself, especially:

- op-amp feedback circuits
- summing nodes / branching analog nets
- dense multi-branch diagrams
- large netlists

If auto layout warns, move to presets or manual overrides instead of fighting the
single default grid.

## Canonical names vs compatibility aliases

Prefer these names in new code:

- `TextPlacementOverride` (not `PlacementOverride`)
- `Port.id` / `Pin.id` (not informal `connection_id` wording)
- `get_port(...)` as canonical component accessor
- `pin_world_position(...)` as canonical geometry helper

Compatibility aliases still exist:

- `get_pin(...)`
- `port_world_position(...)`

They are kept for migration safety, but new examples and docs use canonical names.

## Export and preview

For static quick checks, export a PNG directly:

```python
diagram = render_circuit_diagram(
    build,
    layout,
    output_path="tmp/preview.png",
)
```

This writes a one-frame PNG preview and reports the resulting `output_path`.

If you also pass `preview=True`, the quickstart layer will attempt to open that
PNG through the host OS when supported. Current behavior:

- `preview=True` **requires** `output_path=...`
- Windows environments can use `os.startfile(...)`
- unsupported hosts return `preview_available=False` and add
  `preview.open_unavailable`

If you only pass `preview=True` without `output_path`, the result adds the
warning `preview.requires_output_path`.

## Where to go next

- Want the low-level layering model: [architecture.md](architecture.md)
- Need component contracts and pin naming: [component-api.md](component-api.md)
- Need layout strategy, presets, and overrides: [layout-strategy.md](layout-strategy.md)
- Want runnable example scenes: [../examples/README.md](../examples/README.md)
