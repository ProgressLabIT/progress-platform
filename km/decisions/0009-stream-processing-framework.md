# 0009 — Stream Processing Framework: Custom Python for v1, Bytewax for v2

**Status:** decided
**Date:** 2026-04-28
**Audience:** S1 (bridge, v1), post-demo workstream owner (v2)
**Supersedes:** none

## Context

The Sparkplug demo's value extension beyond a viewer is the path
"Sparkplug metric → Progress event" — automations that turn telemetry into
MES actions. v1 demo ships a single hardcoded automation in Python (per
ADR-0010); v2 expands this into a configurable engine with a YAML rule
file.

The choice of stream-processing substrate for v2 affects code shape, the
operator vocabulary, the recovery story, and the long-term ceiling of how
much logic the engine can express. This ADR captures the decision to use
**Bytewax 1.x** for v2 and the rationale, recorded now while context is
fresh, even though v2 implementation is post-demo.

The sparkplug-demo workstream's `research/SUMMARY.md` originally rejected
Bytewax as "abandoned" based on a single Medium article and observed
GitHub inactivity. That assessment is incorrect: Bytewax went through a
v0→v1 rewrite (Rust core, Python API), is actively maintained, and has
commercial backing. This ADR supersedes that judgment.

## Decision

### v1 demo: custom Python in the bridge (per ADR-0010)

For the May 15 demo, the automation lives as plain Python inside the
Sparkplug bridge process: ~50–80 lines, hardcoded threshold + dwell +
latch, hardcoded link list, single subject subscription. This avoids any
new framework dependency and any framework-shaped learning curve during a
tight 11-day window.

The automation code is a single self-contained module
(`backend/sparkplug_bridge/automations/pump_anomaly.py`) and the bridge's
main loop calls into it on each decoded NDATA frame. No queue, no
scheduler, no state-machine framework — just an `if` and a few
`asyncio.sleep`-based timers.

### v2 (post-demo): Bytewax-driven binding engine

After the demo, the post-demo workstream replaces the hardcoded automation
with a Bytewax-based engine:

- `backend/bindings/` becomes a separate Python service (no longer
  in-bridge).
- The service reads `bindings.yaml` (revised schema based on superseded
  ADR-0003 plus generic-subject extensions).
- Each binding compiles to a Bytewax dataflow:
  `flow.input(NATSSource).filter(match).window(dwell).filter(operator).map(latch).map(render_payload).output(HTTPSink)`.
- Bytewax handles the operator graph, windowed state, recovery, and
  metrics.
- The bridge stays focused on Sparkplug protocol concerns; bindings become
  a generic NATS-subject reactor reusable for non-Sparkplug producers
  (production events, future agent emissions, etc.).

The v2 work is captured as a phase in `REQUIREMENTS.md` `## Post-Demo`
under a new `BIND-ENGINE-*` requirement set; the original BIND-* items
remain as the surface-area definition.

### What Bytewax buys us in v2

- **Operator graph as a first-class abstraction.** Each binding is a
  composition of standard operators (filter, map, window, fold, output),
  which makes a YAML schema clean to validate (each YAML rule maps to a
  small, fixed set of operators).
- **Stateful windowing.** Dwell time, rate-of-change, hysteresis, and
  multi-frame conditions all become standard window operators. The
  hardcoded v1 dwell timer becomes a one-line `flow.window(...)` call.
- **Recovery.** Bytewax's snapshot model lets a restarted engine resume
  from a known offset; the v1 hardcoded automation has no recovery story.
- **Metrics + observability.** Bytewax exposes per-operator throughput,
  lag, and error counts; v1 hardcoded automation logs at the python-`log`
  level only.
- **Future stream-processing reuse.** Anomaly detection, rolling
  aggregations, cross-source joins (Sparkplug × work-order events) all
  compose naturally on the same dataflow runtime.

### Why Bytewax over alternatives

- **Apache Flink / Beam.** JVM ecosystem, operationally heavyweight, far
  beyond v2's needs. Reject for the same reasons we don't run Kafka.
- **Faust (Robinhood).** Mature but Kafka-tied historically; NATS support
  exists via community ports but is not first-class.
- **Benthos / Redpanda Connect.** Go runtime, declarative pipeline DSL,
  ergonomic for transforms but its model fights stateful Sparkplug-style
  bdSeq + alias resolution. Already evaluated and rejected for the bridge
  proper.
- **PyFlink.** Python wrapping a JVM runtime; high operational complexity
  for our scale.
- **Plain asyncio (v1's choice).** Works for one rule; doesn't compose
  into a YAML-configurable engine without re-inventing operators.

Bytewax fits because: pure Python deployment, NATS source/sink available
or trivially writable, operator graph abstraction matches the YAML config
shape we want, scale ceiling far above demo scale.

### Migration path from v1 to v2

The v1 hardcoded automation produces the same external observable
behaviour as a future Bytewax-based binding: same NATS subscription, same
HTTP POST, same payload. v2 replaces the implementation behind that
contract; restored DB content, simulator scenario, demo bindings.yaml-shape
all carry forward.

## Trade-offs and rejected options

**Use Bytewax for v1 demo too.** Rejected. 11 working days does not
accommodate framework adoption alongside the Sparkplug protocol work and
the rest of the demo scope. The hardcoded path is correct for v1.

**Skip v2 commitment.** Considered keeping v2 framework choice open. Locking
it now is cheap (this ADR) and lets post-demo work start immediately
without a second framework-evaluation phase.

**Build a custom in-house engine instead of adopting Bytewax.** Rejected.
Stream-processing operator semantics (windowing, recovery, fault tolerance)
are well-trodden territory; reinventing for a generic engine is a year of
work for a feature that would still be inferior to off-the-shelf.

**Use the original "abandoned" Bytewax v0.** Rejected (and incorrect
framing). Bytewax v1 (current) is the supported library; v0 is end-of-life.

## Consequences

- v1 demo ships custom Python (per ADR-0010); no Bytewax dependency.
- v2 plan in `REQUIREMENTS.md` `## Post-Demo` will reference this ADR for
  framework choice.
- The superseded ADR-0003 schema sketch is the v2 starting point for the
  YAML user-facing surface, refined with Bytewax operator vocabulary.
- The KM intro doc (`km/architecture/sparkplug.md`) mentions the v2 plan
  in its roadmap section.

## Related

- ADR-0003 — original YAML binding schema, superseded by ADR-0010 for
  v1 but useful as the v2 starting design.
- ADR-0010 — hardcoded v1 automation; the implementation Bytewax will
  replace post-demo.
- Bytewax documentation: <https://bytewax.io/docs>
- `research/SUMMARY.md` — note that the original Bytewax-as-abandoned
  judgment is superseded by this ADR.
