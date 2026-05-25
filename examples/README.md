# Examples

Analog-first teaching examples with minimal protocol/basic smoke retained for
regression coverage.

## Prerequisites

```bash
pip install -e .
pip install -e ".[manim]"
```

## Smoke checks (no Manim render)

```bash
python examples/basics/graph_only.py
python examples/protocol/spi_byte_transfer.py
```

## Manim previews

```bash
manim --disable_caching -pql examples/analog/01_rc_charge.py RCChargeScene
manim --disable_caching -pql examples/analog/03_cmos_inverter.py CMOSInverterScene
manim --disable_caching -pql examples/analog/09_mos_four_types.py MosFourTypesScene
manim --disable_caching -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo
```

**Cache:** after changing library code, pass `--disable_caching` or delete
`media/videos/<scene>/partial_movie_files/` to avoid stale renders.

## Catalog

- Analog scene catalog: [analog/README.md](analog/README.md)
- Minimal protocol smoke: `protocol/spi_byte_transfer.py`
- Minimal basic smoke: `basics/graph_only.py`
