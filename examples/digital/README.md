# Digital Examples

Digital teaching examples for component and renderer smoke coverage.

## Catalog

| File | Concept | Components | Run command |
|------|---------|------------|-------------|
| `logic_gate_chain.py` | A/B fanout into AND/OR, with AND output inverted | A, B, AND, OR, NOT | `manim --disable_caching -pql examples/digital/logic_gate_chain.py LogicGateChainScene` |

## Fixture Smoke Contract

Digital examples expose `build_*_fixture()` helpers so tests can validate
topology and layout deterministically without Manim rendering.
