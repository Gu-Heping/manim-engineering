# Agent Guide

Long-term AI-assisted development on a **semantic-first** Manim engineering framework.

## Read first

1. [.cursor/rules/00-foundation.md](.cursor/rules/00-foundation.md) — layers, priorities, repo layout
2. [docs/ROADMAP.md](docs/ROADMAP.md) — current phase and task boundaries
3. Domain rule for your task (semantic, protocol, renderer, etc.)

Do not re-derive architecture from `docs/` alone; rules are authoritative.

## Rule index

| File | Use when |
|------|----------|
| `00-foundation.md` | Any change — layer and directory ownership |
| `10-engineering-standards.md` | Code, API, forbidden patterns |
| `20-semantic-core.md` | Signals, topology, propagation |
| `30-timing-waveform.md` | Clocks, traces, sync |
| `40-protocol-modeling.md` | UART/SPI/I2C/CAN |
| `50-layout-routing.md` | Placement, routing, occupancy |
| `60-renderer-philosophy.md` | Renderers, themes |
| `70-component-authoring.md` | New components |
| `80-animation-and-education.md` | Motion, scenes, pacing |
| `90-testing-and-workflow.md` | Tests, examples, diff discipline |

## Long-task protocol

### Before starting

- Confirm phase in `docs/ROADMAP.md` matches your work
- Scope to **one** subsystem per session (one layer or one vertical slice)
- List: semantic owner, files to touch, tests to add

### Implementation order

```text
semantic → component → rendering → animation → tests → example
```

Never start from Manim geometry or decorative motion.

### Per-task checklist

- [ ] Correct layer; no forbidden imports
- [ ] Reused existing abstractions (no duplicate systems)
- [ ] Minimal diff; no unrelated refactors
- [ ] Unit tests + minimal executable example
- [ ] No `except: pass`; no `signal.color`, `NMOS(renderer=...)`, `component.animate_*`

### Forbidden

- Speculative abstractions without immediate use
- Architecture rewrites in feature PRs
- Bypassing semantic APIs for convenience
- Giant demos mixing unrelated concepts

## Human reference docs

| Doc | Content |
|-----|---------|
| [docs/architecture.md](docs/architecture.md) | Layer diagram, directories |
| [docs/component-api.md](docs/component-api.md) | `CircuitElement` contract |
| [docs/visual-theme.md](docs/visual-theme.md) | Color/background constants |
| [docs/animation-timing.md](docs/animation-timing.md) | Duration guidelines |

## Conflict resolution

Rule precedence (high → low): Foundation → Semantic → Layer boundaries → Domain → Renderer → Layout → Animation → Education → Engineering standards → Testing/workflow.
