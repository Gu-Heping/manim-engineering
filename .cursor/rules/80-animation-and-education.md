# Animation and Education

Animation explains behavior; scenes orchestrate understanding. Both consume semantic systems.

## Animation Goals

Clarify: causality, propagation direction, timing, state transitions, focus hierarchy.

Every motion MUST map to a purpose: `propagation` | `timing` | `focus` | `transition`.

Forbidden: decorative motion, ambiguous direction, competing simultaneous emphasis.

## Signal Propagation (animation)

Visualize semantic propagation metadata (source→destination). Techniques: traveling highlights, pulses, edge propagation, waveform-linked motion.

Forbidden: visual-only propagation without semantic backing.

## Motion Hierarchy

1. active signal  
2. active component  
3. subsystem context  
4. background structure  

Dim inactive systems; isolate active paths.

## Pacing

Rhythm: introduce structure → isolate focus → trigger change → observe propagation → pause.

Include deliberate pauses after major transitions and timing-critical events.

## Progressive Reveal (scenes)

Order: global structure → subsystem grouping → active path → local mechanism → timing nuance → edge cases.

Never expose full complexity at once.

## Teaching Density

**At most 2 concepts per scene moment.** One preferred.

Educational simplification allowed: exaggerated delay, enlarged pulses, simplified symbols — semantic APIs still required.

## Scene Responsibilities (`examples/` / scene scripts)

Orchestrate: pacing, focus order, abstraction transitions.

Must compose reusable primitives (`SignalFlow`, `WaveformSync`, `VoltagePulse`) — no duplicated animation logic or hidden timing hacks.

## Camera

Guide attention, isolate regions, reveal relationships. Forbidden: cinematic drift, constant zoom, dramatic spins.

## Domain Motion

**Analog**: smooth continuous interpolation aligned with semantic state.  
**Digital**: discrete, edge-triggered, synchronized steps.  
**Protocol**: sync, ordering, ownership visible (see `40-protocol-modeling.md`).

## Transitions

Preserve mental continuity (transforms, guided movement). Forbidden: teleportation, unexplained layout jumps.

## Reusable Primitives

Prefer shared animation abstractions over scene-specific hacks.
