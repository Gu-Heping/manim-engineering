# Protocol Modeling

Protocols are semantic timing systems in `protocol/`. Not moving lines or decorative packets.

## Semantic Model (required before render/animate)

Define explicitly:

1. sender / receiver / bus ownership
2. edge timing, sync windows, propagation delay
3. framing (start/stop, address, payload, parity, ACK)
4. arbitration semantics (priority, contention resolution)
5. deterministic state machine

## Ownership

Bus ownership is semantic — never inferred from visuals.

Examples: SPI master/slave, I2C arbitration, CAN priority, UART TX/RX roles.

## Per-Protocol Focus

**UART**: async timing, start/stop framing, baud/sample points — explain baud mismatch and framing failure.

**SPI**: clock/data alignment, CS, mode timing — clock edges drive dependent state.

**I2C**: open-drain, ACK timing, addressing, arbitration, clock stretch.

**CAN**: arbitration priority, dominant/recessive, non-destructive arbitration outcome.

## Rendering & Animation

Rendering emphasizes directionality, ownership, active paths, timing relationships.

Animation shows communication flow and timing dependency — no decorative packet motion.

## Waveform Sync

Protocol waveforms MUST reflect semantic state, ownership, and timing events (see `30-timing-waveform.md`).

## Implementation Order

1. semantic ownership and timing
2. synchronization and arbitration behavior
3. waveform linkage
4. rendering
5. animation
