# CODE_STYLE (for AI engineers)

## Style priorities

1. Semantic clarity.
2. Stable APIs.
3. Deterministic behavior.
4. Small diff surface.

## Structural rules

- One major abstraction per module.
- No dumping modules (`utils.py`, `helpers.py`, `misc.py`).
- Public APIs must have explicit type hints.
- Prefer dataclasses for structured immutable-like contracts.

## Naming rules

- Use engineering nouns/verbs (`SignalFlow`, `LayoutEngine`, `WaveformTrace`).
- Avoid “smart/magic/ultimate”-style names.
- Pin names stay lowercase and domain-stable.

## API design rules

- Prefer explicit calls over hidden mode switches.
- Keep constructors small and composable.
- Do not encode renderer/animation selection inside components.

## Error handling

- Raise typed exceptions with actionable context.
- No broad `except:` swallowing.
- Preserve cause chain in orchestration-level wrappers.

## Test policy (implementation-level)

- Behavior change -> corresponding test change.
- Bugfix -> regression test or reproducible smoke path.
- Scene choreography change -> animation + examples coverage.
- Geometry change -> geometry gate suite.

## Diff discipline

- Avoid opportunistic refactors in feature PRs.
- Separate docs-only from behavior changes when feasible.
- Keep naming and ownership consistent with existing conventions.

## Documentation style for this project

- Write contracts, boundaries, failure modes.
- Avoid generic promotional prose.
- Include “why this exists” and “what breaks if changed”.

