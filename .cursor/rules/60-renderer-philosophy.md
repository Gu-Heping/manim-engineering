# Renderer Philosophy

Renderers project semantic meaning into visuals. They do not define engineering meaning.

## Responsibilities

**May**: symbols, geometry, stroke styles, typography, theme colors, labels, visual hierarchy.

**Must not**: topology, signal ownership, timing semantics, protocol behavior, global routing ownership, animations.

## Usage

```python
renderer.render(component)   # correct
NMOS(renderer="ieee")        # forbidden
renderer.animate_signal()    # forbidden — use SignalFlow
```

## Themes

Colors and stroke styles live in renderer themes mapped from semantic kinds (see `10-engineering-standards.md`). Semantic objects stay unstyled.

Multiple renderer families allowed (`ieee/`, `iec/`, `minimal/`, `educational/`) for the same semantic object.

## Layout Interaction

Consume layout hints; do not own global topology placement or routing.

## Educational Simplification

Allowed: enlarged pins, simplified symbols, exaggerated spacing — clarity over drafting realism.

## Quality

- Internally consistent spacing, line width, typography within a renderer
- Deterministic output: no random geometry or unstable ordering
- Snapshot-testable where applicable

## Implementation Order

See `00-foundation.md` § Implementation Order.
