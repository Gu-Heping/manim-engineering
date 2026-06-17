# Measurement Examples

Measurement examples show probes as semantic circuit elements. They are not
simulation instruments; they provide stable ports and renderer symbols for
teaching diagrams.

## Catalog

| File | Concept | Components | Run command |
|------|---------|------------|-------------|
| `probe_chain.py` | Inline current probe plus node voltage probe | IN, IP, Rsense, VP, GND | `manim --disable_caching -pql examples/measurement/probe_chain.py MeasurementProbeScene` |

## Smoke check

```bash
python examples/measurement/probe_chain.py
```
