# Documentation

## Authority

| Type | Location | Purpose |
|------|----------|---------|
| **Rules** (enforced) | [../.cursor/rules/](../.cursor/rules/) | Architecture, constraints, workflow |
| **Reference** (this folder) | `docs/*.md` | Diagrams, API contracts, theme constants |
| **Tasks** | [ROADMAP.md](ROADMAP.md) | Phased implementation for long-running work |

On conflict, `.cursor/rules/` wins. Visual geometry invariants: `31-visual-geometry.md`.

## Reference files

| File | Contents |
|------|----------|
| [quickstart-draw-circuit.md](quickstart-draw-circuit.md) | Fastest task-driven path from components + connections to a diagram |
| [component-catalog.md](component-catalog.md) | Available components, typical pin names, and example index |
| [architecture.md](architecture.md) | Layer diagram, directory map, dependency rules |
| [component-api.md](component-api.md) | `CircuitElement` required API |
| [visual-theme.md](visual-theme.md) | Semantic colors, backgrounds, line hierarchy |
| [animation-timing.md](animation-timing.md) | Suggested animation durations and pacing |
| [visual-validation.md](visual-validation.md) | Golden pipeline overview (executable gates in `90-testing-and-workflow.md`) |

## Removed / merged

- `philosophy.md` — mission and priorities live in `00-foundation.md` and [README.md](../README.md)
- `animation-principles.md` → split: rules in `80-animation-and-education.md`, timings in `animation-timing.md`
- `rendering-guidelines.md` → `visual-theme.md`
- `component-spec.md` → `component-api.md`

## For agents

Start at [../AGENTS.md](../AGENTS.md).
