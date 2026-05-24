# manim-engineering

Semantic engineering visualization framework on [Manim](https://www.manim.community/). Models engineering **meaning** first; renderers and animations project that meaning for teaching.

**Not**: EDA, SPICE, motion graphics. **Is**: explainability, signal flow, timing, reusable educational primitives.

## Documentation map

| Audience | Start here |
|----------|------------|
| Contributors / AI agents | [AGENTS.md](AGENTS.md) |
| Implementation phases (long tasks) | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Human reference | [docs/README.md](docs/README.md) |
| Enforced constraints | [.cursor/rules/](.cursor/rules/) |

**Precedence**: `.cursor/rules/` overrides `docs/` on conflict.

## Architecture (summary)

```text
semantic → component → rendering → animation
```

Extended paths: `layout/`, `protocol/`, `waveform/` (see [docs/architecture.md](docs/architecture.md)).

## Repository status

Phases 0–8 are complete and the example layer is now in **analog-first stabilization**: analog `01`–`08` scenes are primary, with minimal smoke retained for `basics/graph_only.py` and `protocol/spi_byte_transfer.py`. Feature backlog (IEC renderer, I2C/CAN, continuous analog physics) stays under **Feature backlog** in the ROADMAP.

## Running examples

Install the package, then run smoke scripts from the repo root.

```bash
pip install -e .
python examples/basics/graph_only.py
python examples/protocol/spi_byte_transfer.py
```

Manim previews need the optional extra:

```bash
pip install -e ".[manim]"
manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo
manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeScene
```

Full catalog, per-directory tables, and all run commands: [examples/README.md](examples/README.md).

## Quick conventions

- All components inherit `CircuitElement`
- Rendering: `renderer.render(component)` — no renderer on constructors
- Animation: `SignalFlow(signal)` — no animation on components
- One concept per scene moment; tests + minimal example per feature

## License

TBD.
