# Demo Brief — Aerospace Mill Live Twin

**Status:** draft for discussion · **Date:** 2026-05-29 · **Audience:** demo planning (internal)
**One-liner:** An interactive digital twin of a large 3-axis gantry mill carving aircraft
wing skins from 25 m aluminium billets — the customer turns the knobs, the real Progress
platform reacts.

---

## Why this demo

The pump scenario proves the pipeline works. This proves the **thesis** — open, event-sourced,
on-prem MOM where traceability is a primitive — for a regulated aerospace buyer. Three facts
make it land:

1. **The part is flight-critical and serialised.** Its machining record *is* the airworthiness
   evidence (AS9100D 8.5.2 / 7.5). Event sourcing means that record exists by construction.
2. **The economics are violent.** Monolithic wing structures are 90–95% material removal; the
   billet is six figures and the cut runs hours-to-days. A fault caught late = scrap a flight
   part *and* lose machine-days. Real-time monitoring has ROI a pump bearing never will.
3. **The customer creates the anomaly with their own hands** — far more memorable than a
   scripted timeline, robust to demo timing, and it *teaches* cause→effect.

## The machine & the signal

A 3-axis gantry mill (X ≈ 25 000 mm, Y ≈ 4 000, Z ≈ 1 000) running an OP-30 wing-skin finish
pass. The headline signal is **spindle torque** (with **power** as the correlated energy line) —
the real workhorse of CNC process monitoring: a cutting-force proxy straight off the drive.

One sensor carries three readable failure modes:

| Signature | Meaning | Beat |
|---|---|---|
| Gradual **rise** | tool wear | headline Issue → recommend tool change |
| **Collapse** toward zero while feeding | tool **breakage** on a flight part | instant "catch it" beat |
| Sharp **spike** | hard spot / near-collision | feed-hold |

Core relationship the customer can feel: `torque ↑` with **depth × feed-per-tooth × tool-wear**,
`power = torque × RPM`. Three levers all push torque toward the limit.

## Architecture — one standalone service

```
┌──────────────── demo-twin (standalone, decoupled from product) ───────────────┐
│  FastAPI: serves control-panel.html (vanilla JS + WebSocket)                    │
│   UI → setpoints (RPM / feed / depth / wear / temp, fault buttons)              │
│   engine → live readouts @ ~5 Hz   ·   asyncio physics loop                     │
└───────────────────────────────────────────────────────────────┬───────────────┘
                                                                 │ normalized JSON
                                                                 ▼ (publish straight to NATS)
              NATS → UNS browser · Timescale historian · Issue automation
                                            (downstream pipeline UNCHANGED — same NATS JSON consumers)
```

The control panel and twin engine collapse into one standalone process. The twin generates its own
physics and does **not** natively speak Sparkplug B, so it publishes **normalized JSON straight onto
NATS** (the `progress.sparkplug.*` subjects the bridge would otherwise emit after decode) — the
platform's real data plane. Encoding into Sparkplug B just so the bridge could decode it straight back
buys nothing; Sparkplug B is reserved for equipment that already emits it. Everything that consumes the
JSON — UNS browser, historian, and the threshold→Issue automation (here a NATS subscriber, not
in-bridge) — is unchanged; only the MQTT/Sparkplug hop is dropped. The customer drives a *twin* feeding
the *real* product pipeline; the *product* (UNS browser + Issues page) reacts.

## The interaction

Drag **Tool wear** (or crank feed/depth) → spindle torque climbs past the limit → 5 s dwell →
an **Issue auto-appears in the real Progress UI**, linked to the wing serial + work order +
operation, attributed to the machine user. Hit **Snap tool** → torque collapses → breakage Issue.
Same `pump_anomaly` logic, retargeted.

## Build scope (small)

| New | Reused as-is |
|---|---|
| `demo-twin/` FastAPI service + asyncio loop | `simulator/physics.py` (dynamics helpers) |
| `control-panel.html` (sliders, gauges, WebSocket) | `simulator/topology.py` (→ gantry metric set) |
| thin NATS JSON publisher → `progress.sparkplug.*` (replaces `simulator/encoder.py` Sparkplug encode) | historian · UNS browser · Issue/event path (NATS-JSON consumers) |
| setpoint→physics map; retarget anomaly to torque + breakage |  |

## Open decisions for Tuesday

1. **Lead anomaly:** tool-wear torque rise (headline) vs. also wiring breakage/hard-spot day one.
2. **Customer framing:** AS9100D traceability angle vs. energy/OEE angle (changes narration, not build).
3. **Data path — decided:** twin publishes normalized JSON straight to NATS (no Sparkplug B — the twin doesn't natively emit it). Point the bridge at a real machine that already speaks Sparkplug B and that ingress lights up unchanged.
4. **Live gauges:** engine WebSocket (default) vs. `nats.ws` round-trip to prove the full loop.
5. **Sim vs. their data:** bundled gantry metrics vs. a metric set shaped like the customer's machine.

## Next step

Scaffold `demo-twin` via `/gsd:quick` once the anomaly + framing are locked.
