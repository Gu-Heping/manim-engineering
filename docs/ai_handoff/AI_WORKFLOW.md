# AI_WORKFLOW (for future Codex agents)

## Start sequence for any non-trivial task

1. Read `.cursor/rules/00-foundation.md`.
2. Read domain rule(s) touched by your task.
3. Read `docs/ROADMAP.md` status + backlog sections.
4. Locate canonical owner module before coding.

If ownership is unclear, stop and resolve ownership first.

## Implementation workflow (enforced style)

1. Confirm layer and owner.
2. Change minimal set of files.
3. Add/adjust tests before broad refactors.
4. Run targeted tests, then broader suite as needed.
5. Keep docs in sync for contract changes.

## Decision tree before adding abstractions

- Does this solve an immediate active use case?
- Is there an existing abstraction that can be extended?
- Does this cross layer boundaries?
- Can this be tested deterministically?

If any answer is bad, redesign.

## High-risk areas (extra caution)

- `waveform/layout.py` geometry contracts.
- `animation/beat.py` and `animation/waveform_reveal.py` reveal sequencing.
- `layout/routing.py` and net waypoint logic.
- label placement and orientation interactions.

## Required validation packs

- Always: `ruff check src tests` + `pytest tests -q` (or targeted while iterating).
- For geometry/render/waveform changes: run geometry smoke bundle from rule 90.
- For scene choreography changes: run animation + examples smoke + manual render sanity.

## PR behavior for AI agents

- One theme per change.
- Separate docs-only and behavior changes when practical.
- Do not silently weaken tests/gates.
- Do not commit/push/merge unless explicitly requested by user.

## Debugging discipline

- Use trace/snapshot env flags for animation sequencing issues.
- Disable Manim cache during framework-level render debugging.
- Prefer root-cause fixes over additional visibility patches.

## What “done” means in this repo

Done means:
- layer-correct,
- deterministic,
- test-backed,
- compatible with scene templates,
- aligned with roadmap direction.

