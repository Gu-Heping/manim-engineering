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
- `layout_mode`: `semantic_grid`, `structured_auto`, or `manual`
- `routing_report`: machine-readable routing diagnostics
- `warnings`: machine-readable warning strings
- `needs_attention`: `True` when the diagram likely needs preset/manual help
- `recommended_action`: coarse next-step guidance for agents and callers

Current warning examples:

- `layout.occupancy_above_target`
- `layout.single_row_auto_grid`
- `layout.branching_topology_using_auto_grid`
- `layout.routing_parallel_overlap`
- `layout.routing_shared_segment`
- `layout.routing_crossing_without_junction`
- `layout.routing_wire_through_component`
- `layout.routing_wire_near_unconnected_pin`

If `needs_attention` is true, do not assume the rendered circuit is acceptable
just because rendering succeeded.

`structured_auto` appears when the quickstart layer detects a branching topology
with no manual placement overrides and compiles a deterministic multi-row fallback
before calling `LayoutEngine`.

`routing_report` is the structured counterpart to those warning strings. It is
the recommended surface for agents or higher-level tooling that need to decide
whether the layout is acceptable or should fall back to presets / overrides.

`routing_report.highest_severity` gives a coarse summary of the remaining
routing risk after current auto-detour and spacing passes:

- `cosmetic`
- `ambiguous`
- `blocking`

`recommended_action` is the quickstart layer's higher-level interpretation of
those residual issues:

- `accept`
- `review_routing`
- `use_preset_or_overrides`

Current mapping is intentionally conservative:

- residual `blocking` issues -> `use_preset_or_overrides`
- residual `ambiguous` issues -> `review_routing`
- single-row auto-grid stress -> `use_preset_or_overrides`
- pure occupancy stress without residual routing ambiguity -> `review_routing`
- clean or fully auto-detoured layouts -> `accept`

In practice this means a layout can be geometrically clean after auto-detour
and still return `review_routing` if it remains unusually dense. The routing is
usable, but the task-level helper is warning that human readability may still
benefit from preset placement or manual refinement.

Current routing issue kinds are:

- `parallel_overlap`
- `shared_segment`
- `crossing_without_junction`
- `wire_through_component`
- `wire_near_unconnected_pin`

`wire_through_component` means the current orthogonal route passes through the
interior of another placed component footprint. The layout layer now tries a
small deterministic dogleg around simple single-segment and two-segment cases;
this warning only remains when no safe local detour succeeded.

`wire_near_unconnected_pin` means a wire passes close enough to an unrelated pin
anchor that the diagram may look falsely connected there. The layout layer now
tries a local deterministic track shift for simple cases; this warning only
remains when no safe local detour succeeded.

`routing_report` therefore describes **residual routing problems after the
current auto-detour passes**, not every intermediate hazard the layout engine
considered while refining the wire geometry.

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
- Windows environments use `os.startfile(...)`
- macOS uses `open`
- Linux/other Unix hosts try `xdg-open`
- unsupported hosts return `preview_available=False` and add
  `preview.open_unavailable`

If you only pass `preview=True` without `output_path`, the result adds the
warning `preview.requires_output_path`.

When the rendered layout contains a non-junction wire crossing, the minimal
renderer now draws that crossing differently from a true electrical junction:

- junctions still render as solid dots
- non-junction crossings get a small background-color crossing mask

That visual distinction comes from `layout.routing_report`; it is not inferred
independently by the renderer.

## Where to go next

- Want the low-level layering model: [architecture.md](architecture.md)
- Need component contracts and pin naming: [component-api.md](component-api.md)
- Need layout strategy, presets, and overrides: [layout-strategy.md](layout-strategy.md)
- Want runnable example scenes: [../examples/README.md](../examples/README.md)
