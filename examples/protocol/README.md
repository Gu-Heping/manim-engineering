# Protocol examples

Protocol-layer semantics with layout, waveforms, and animation sync (SPI and UART).

## Table

| File | Phase | Concept | Key abstractions |
|------|-------|---------|------------------|
| `spi_byte_transfer.py` | 7 | Mode-0 byte transfer, FSM, clk/mosi/miso/cs waveforms | `SPIBusBinding`, `SPIController.transfer_byte`, `SPIMaster`, `SPISlave`, `derive_bundle_from_signals`, `SignalFlow`, `WaveformSync` |
| `uart_byte_transfer.py` | 9 | 8N1 byte TX, start/data/stop framing, LSB-first | `UARTBinding`, `UARTController.transmit_byte`, `UARTPort`, `derive_bundle_from_signals`, `SignalFlow`, `WaveformSync` |

## Run commands

Smoke (no video):

```bash
python examples/protocol/spi_byte_transfer.py
python examples/protocol/uart_byte_transfer.py
```

Manim preview:

```bash
manim -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo
manim -pql examples/protocol/uart_byte_transfer.py UARTByteTransferDemo
```

Expected smoke output includes step count, byte value, FSM state, trace names, and `SignalFlow` / sync timing metadata.
