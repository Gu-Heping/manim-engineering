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
| `31-visual-geometry.md` | scene_bbox, waveform gap, z-order |
| `60-renderer-philosophy.md` | Renderers, themes |
| `70-component-authoring.md` | New components |
| `80-animation-and-education.md` | Motion, scenes, pacing |
| `90-testing-and-workflow.md` | Tests, examples, diff discipline, visual goldens, **PR delivery** |

## Workflow

Task sizing, implementation order, per-task checklist, and forbidden patterns: see [`.cursor/rules/90-testing-and-workflow.md`](.cursor/rules/90-testing-and-workflow.md).

### Delivery workflow

Default path for shipping changes:

**feature branch → PR → CI green → actionable review addressed → squash merge**

Full branch naming, pre-push gates, review triage, fix loop, and merge criteria: [`.cursor/rules/90-testing-and-workflow.md` § PR and merge workflow](.cursor/rules/90-testing-and-workflow.md#pr-and-merge-workflow).

**Agent constraints** (repo policy):

- Do **not** commit, push, open a PR, or merge unless the user explicitly asks.
- When the user asks to merge: do **not** merge while CI is failing or actionable review items remain unresolved (unless the user accepts the risk in the PR thread).

## Human reference docs

| Doc | Content |
|-----|---------|
| [docs/architecture.md](docs/architecture.md) | Layer diagram, directories |
| [docs/component-api.md](docs/component-api.md) | `CircuitElement` contract |
| [docs/visual-theme.md](docs/visual-theme.md) | Color/background constants |
| [docs/animation-timing.md](docs/animation-timing.md) | Duration guidelines |
| [docs/mosfet-symbols.md](docs/mosfet-symbols.md) | Four MOSFET types + switchable conventions |
| [docs/layout-strategy.md](docs/layout-strategy.md) | Grid vs preset vs override; deferred auto-placer |
| [docs/visual-validation.md](docs/visual-validation.md) | Golden pipeline overview (gates in rule 90) |

## Conflict resolution

Rule precedence (high → low): Foundation → Semantic → Layer boundaries → Domain → Renderer → Layout → Animation → Education → Engineering standards → Testing/workflow.
