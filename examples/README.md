# Examples

Analog-first teaching examples with minimal protocol/basic smoke retained for
regression coverage. Digital gate examples cover basic logic-symbol rendering.

## Prerequisites

```bash
pip install -e .
pip install -e ".[manim]"
```

## Fastest way to assemble a static circuit

If you are not trying to render a full teaching scene yet, start with
[../docs/quickstart-draw-circuit.md](../docs/quickstart-draw-circuit.md). It
documents the task-level `build_circuit(...) -> layout_circuit(...) ->
render_circuit_diagram(...)` path.

## Smoke checks (no Manim render)

```bash
python examples/basics/graph_only.py
python examples/digital/logic_gate_chain.py
python examples/measurement/probe_chain.py
python examples/renderers/iec_resistor.py
python examples/protocol/spi_byte_transfer.py
```

## Manim previews

```bash
manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeScene
manim --disable_caching -pql examples/analog/03_cmos_inverter.py CMOSInverterScene
manim --disable_caching -pql examples/analog/09_mos_four_types.py MosFourTypesScene
manim --disable_caching -pql examples/digital/logic_gate_chain.py LogicGateChainScene
manim --disable_caching -pql examples/measurement/probe_chain.py MeasurementProbeScene
manim --disable_caching -pql examples/renderers/iec_resistor.py IECResistorScene
manim --disable_caching -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo
```

**Cache:** after changing library code, pass `--disable_caching` or delete
`media/videos/<scene>/partial_movie_files/` to avoid stale renders.

## Catalog

- Analog scene catalog: [analog/README.md](analog/README.md)
- Digital scene catalog: [digital/README.md](digital/README.md)
- Measurement scene catalog: [measurement/README.md](measurement/README.md)
- Renderer variant catalog: [renderers/README.md](renderers/README.md)
- Minimal protocol smoke: `protocol/spi_byte_transfer.py`
- Minimal basic smoke: `basics/graph_only.py`
