# Demo Brief — Aerospace Mill Live Twin

**Status:** built — v1.0 code-complete, DEMO-01 rehearsal-ready · **Date:** 2026-05-29 (updated 2026-06-18) · **Audience:** demo planning (internal)
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
JSON — UNS browser, historian, and the threshold→Issue automation (the standalone `mill_automation`
NATS subscriber, not in-bridge) — is unchanged; only the MQTT/Sparkplug hop is dropped. The customer
drives a *twin* feeding the *real* product pipeline; the *product* (UNS browser + Issues page) reacts.

## The interaction

Drag **Tool wear** to max **and** raise **feed/tooth** → spindle torque climbs past the **45 N·m limit**
(`torque ∝ depth × feed/tooth × (1 + 0.5·wear)`; wear alone tops out ~39 N·m, so a second lever is
needed) → ~5 s dwell → an **Issue auto-appears in the real Progress UI**, linked to the wing serial +
work order + operation, attributed to the machine user. Hit **Snap tool** → torque collapses → breakage
Issue (instant, no dwell). Implemented as the standalone `mill_automation` subscriber — the `pump_anomaly`
threshold logic, retargeted to torque.

## Build scope (as built)

| New | Reused as-is |
|---|---|
| `demos/mill_twin/demo_twin/` FastAPI service + asyncio physics loop | `simulator/physics.py` (dynamics helpers) |
| `static/control-panel.html` + `config.js` (sliders, gauges, `nats.ws` WebSocket) | `simulator/topology.py` (→ gantry metric set) |
| thin NATS JSON publisher → `progress.sparkplug.*` (replaces `simulator/encoder.py` Sparkplug encode) | historian · UNS browser · Issue/event path (NATS-JSON consumers) |
| `demos/mill_twin/mill_automation/` threshold→Issue NATS subscriber (`pump_anomaly` logic, retargeted to torque + breakage) |  |

## Decisions (resolved)

1. **Lead anomaly — resolved:** tool-wear torque rise is the headline DEMO-01 beat; **Snap-tool** breakage is wired as the instant backup beat (no dwell). Hard-spot/spike is not wired.
2. **Customer framing — narration choice:** AS9100D traceability vs. energy/OEE angle — both are supported by the same build; pick per audience.
3. **Data path — decided:** twin publishes normalized JSON straight to NATS (no Sparkplug B — the twin doesn't natively emit it). Point the bridge at a real machine that already speaks Sparkplug B and that ingress lights up unchanged.
4. **Live gauges — resolved:** the panel subscribes to NATS over WebSocket (`nats.ws`) — the connect chip proves the full loop. Anonymous WS connections map to a restricted sub-only `ws_browser` identity (the browser sends no credentials).
5. **Sim vs. their data — resolved:** the bundled gantry metric set ships; a customer-shaped metric set is deferred.

## Operating it

The demo is built and rehearsal-ready (local compose **and** the deployed Swarm/HTTPS server).
For run/reset/kill-switch steps, smoke checks, and troubleshooting see the
[Rehearsal Runbook](aerospace-mill-twin-demo-runbook.md).
