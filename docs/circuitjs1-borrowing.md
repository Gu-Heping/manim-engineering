# circuitjs1 Borrowing Plan (Isolated)

This project focuses on teaching-first animation semantics, not full SPICE-grade
simulation. We borrow design ideas from circuitjs1 selectively, without runtime
coupling to the current Manim pipeline.

## What to borrow

- `stamp()` style component contributions for linear algebra assembly.
- `doStep()` style per-step updates for time-varying or nonlinear behavior.
- Matrix-size awareness (avoid over-growing unknown sets when not needed).

## What not to borrow (for now)

- Full nonlinear solver loop as a hard dependency in scene rendering.
- Direct replacement of `Signal` propagation history with matrix solutions.
- Any integration that blocks deterministic teaching beats and captions.

## Mapping to this repo

| circuitjs1 concept | candidate location here | status |
|---|---|---|
| `stamp()` | `experiments/circuitjs1_stamp_prototype.py` | prototype only |
| `doStep()` | `experiments/circuitjs1_stamp_prototype.py` | prototype only |
| matrix solve | isolated experiment script | prototype only |
| runtime scene coupling | `examples/_shared.py` / `animation/*` | intentionally not used |

## Decision gate

Promote ideas only when all of the following hold:

1. Improves teaching explainability (clearer cause/effect in captions and beats).
2. Keeps scene determinism (`pytest` + visual golden stability).
3. Does not force large architectural rewrites in `core/semantic/layout/renderers`.

If a prototype fails any gate, keep current semantic propagation model.
