# NATS-native CEP library — shaping notes

> **Status: WORKING NOTES, nothing decided.** Not an ADR. Captures the direction from the
> 2026-06-01 stream-processing/CEP discussion (research threads "IIoT1–6") so we can shape it
> further. Do not treat anything here as locked until promoted to an ADR.

## Where this came from

The demo-era plan (ADR-0009, in the `sparkplug-demo` workstream, off-DEV) locked **Bytewax** as
the v2 binding/stream-processing engine. Post-demo research re-opened that: Bytewax is in caretaker
mode, and an 8-engine evaluation (Proton, Arroyo, RisingWave, eKuiper, Feldera, Tremor, …) plus a
deeper look at what manufacturing CEP actually needs pointed somewhere else. These notes are the
"boil it down" pass.

## Tentative direction: 3-tier, no monolithic engine

1. **Analytics / KPI / gap-detection → TimescaleDB** (already in the stack). Continuous
   aggregates, `NOT EXISTS` gap queries, OEE/throughput/defect-rate. Don't add Proton — it's a
   second stateful store overlapping Timescale.
2. **Absence / sequence / SLA-timer CEP → NATS-native saga**, owned by the event-sourced MES.
   This is the part that replaces the hardcoded v1 automation *and* the Bytewax v2 plan.
3. **Edge windowing / threshold / compound → eKuiper, optional**, only where edge-local
   (sub-second act-back-to-PLC, bandwidth) genuinely matters. Default: skip, keep in pocket.

→ This direction **would supersede ADR-0009** and require updating `km/architecture/iiot-architecture.md`
and `km/architecture/sparkplug.md` (both still describe the Bytewax binding engine). Deferred until shaped.

## The thing to build: complementary OSS NATS-CEP library

- **Ingest:** via NATS, source-agnostic (ThingsBoard Gateway, Telegraf, custom Python — don't care).
- **State/transport:** embedded NATS listeners/publishers + KV + object store. No new infra — "it's
  just your NATS" is the differentiator for air-gapped, solo-maintained IIoT.
- **CEP logic:** config-driven, a YAML DSL inspired by Benthos/Bloblang, JSONata, CEL.
- **Relationship to Progress:** complementary, not bundled. Progress (event-sourced MES) is the
  natural owner of the saga/expectation state.

## Scope boundaries (the discipline that keeps it from becoming a worse Flink)

- **Target the business-event tier, not sensor-rate.** Hz–low-kHz. State a msg/s ceiling in the README.
- **Own** correlation / absence / sequence / SLA-timer patterns.
- **Delegate** windowed aggregation to Timescale / eKuiper. At most trivial count/last/sum, documented.
- **Refuse** sensor-rate CEP (10k–100k msg/s) — that's where the durable-write model dies.
- **DSL = two layers:** reuse CEL/JSONata for the *stateless* per-event predicate/projection layer;
  design a small **closed** pattern vocabulary (within / not-within / sequence / count) for the
  temporal layer. Resist Esper-EPL completeness. The temporal layer is the moat *and* the risk.

## Validated mechanism: NATS per-key TTL markers (spike 2026-06-01)

Server-owned timer for absence detection. Spiked on real NATS 2.12.6 + nats-py 2.14.0, cross-checked
with the Go `nats` CLI. Full detail in memory `reference_nats_kv_ttl_cep_spike`. Headlines:

- **Distinguishable:** TTL-expiry marker = `Nats-Marker-Reason: MaxAge` + `Nats-Rollup: sub`, nil
  body, no `KV-Operation`. Explicit close = `KV-Operation: DEL/PURGE`. Three-way: MaxAge=timeout,
  DEL/PURGE=close, else=open.
- **Landmine:** nats-py `kv.watch()` reports the expiry marker as `operation=None` (a PUT) → silently
  misses every timeout. **Consume the raw KV stream (`$KV.<bucket>.>`) with a durable pull consumer
  and read headers.** Never `kv.watch()`.
- **Constraint:** effective per-key TTL = `max(requested, bucket marker_ttl)`. `marker_ttl` floors the
  minimum expressible timeout *and* sets the marker observation window (one knob) → one bucket per
  SLA-granularity class.
- **Constraint:** expiry marker rolls up history (`Nats-Rollup: sub`) → sequence gaps → ordered push
  consumers stall; durable pull tolerates them.
- **Latency:** server sweep ≈ 250ms → detection 0–260ms past deadline (idle). Near-real-time gap is
  sub-¼s, not 1s. Make timeouts retractable (compensating event) so late edge-buffered closes self-heal.

## Real-world limits to keep honest about

- **Timer durability vs scale:** server TTL handles it now; the reconciliation backstop covers
  consumer-downtime > marker lifetime. Don't hand-roll a distributed timer wheel.
- **Watcher is effectively a singleton per bucket** — HA/throughput needs keyspace partitioning we'd
  have to build. v1: single writer per bucket, SPOF documented.
- **Write amplification:** every transition is a durable KV op. Fine at business-event rate, fatal at
  sensor rate. This is the same property — asset here, liability there.
- **Ordering / event-time:** cross-subject order isn't guaranteed; v1 = arrival-time + "in-order within
  subject," stated explicitly. Out-of-order/late = compensation, not a fat margin.
- **At-least-once output:** no atomic publish+CAS → downstream must be idempotent (fits event-sourcing).
- **DSL novelty:** LLM has corpus for CEL/JSONata, none for our pattern grammar — the most valuable part
  is the hardest to LLM-author. Keep the grammar small.
- **Gut-check:** durable timer + state + replay ≈ 30% of reinventing Temporal/durable-execution. Be able
  to defend hand-rolling on KV (no-new-infra + native NATS + IIoT DSL) vs "just run it on Temporal."

## Open questions to shape next

- DSL grammar: exact closed pattern vocabulary; where CEL/JSONata stops and the temporal layer starts.
- Throughput envelope: real msg/s numbers (KV put/CAS cost under R=1 vs R≥1).
- Saga ownership concretely: long-lived NATS consumer service in `backend/`? Prefect flow? separate process?
- Bucket strategy: how many SLA-granularity classes; retention/reaping of closed/timed-out keys.
- Repo / naming / license for the OSS library.
- Whether/when to formally supersede ADR-0009 and update the km/architecture specs.
- Edge tier: confirm whether eKuiper is in scope at all for v1.

## Pointers

- ADR-0009 (Bytewax, to be superseded): git `9fda3bee:.planning/workstreams/sparkplug-demo/decisions/0009-stream-processing-framework.md`
- km specs still asserting Bytewax: `km/architecture/iiot-architecture.md` (data-flow + open-question #3), `km/architecture/sparkplug.md` (§ binding engine)
- Spike detail: memory `reference_nats_kv_ttl_cep_spike`
- Source discussion: `.specstory/history/2026-06-01_08-57-04Z-do-we-have-any.md`
