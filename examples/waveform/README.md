# Waveform examples

Waveform traces, bundles, panel layout, and `WaveformSync` timing. **Canonical script** (Phase 6 exit example):

[`../basics/clock_data_waveform.py`](../basics/clock_data_waveform.py)

## What it demonstrates

| Topic | APIs |
|-------|------|
| Clock + data signals on a small net | `Signal`, `SignalType.CLOCK` / `DATA` |
| Trace derivation | `derive_bundle_from_signals` |
| Panel under circuit layout | `WaveformPanelRenderer` |
| Aligned beats with propagation | `SignalFlow`, `WaveformSync` |

Protocol waveforms reuse the same pipeline — see [`../protocol/spi_byte_transfer.py`](../protocol/spi_byte_transfer.py).

## Run commands

Smoke:

```bash
python examples/basics/clock_data_waveform.py
```

Manim preview:

```bash
manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo
```

A dedicated `examples/waveform/*.py` copy is intentionally omitted to avoid drift; add one here only when it teaches a new waveform concept not covered above.
