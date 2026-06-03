# 0003 — bindings.yaml Schema for the Slim MES Wedge

**Status:** superseded by ADR-0010 on 2026-04-28
**Date:** 2026-04-28
**Audience:** S1 (bridge), S3 (slim wedge), S5 (demo data)
**Supersedes:** none
**Superseded by:** [ADR-0010](0010-hardcoded-automation-for-v1-demo.md)

> **NOTE:** The original v1 plan was a YAML-driven binding rule loaded by the
> bridge. After review on 2026-04-28, the demo cut shifted further: v1 ships a
> hardcoded Python automation (~50-80 lines) instead of a YAML-driven engine,
> and the proper engine + YAML config + separate service is deferred to v2 on
> top of Bytewax (see ADR-0009). The body of this ADR is preserved as
> historical context for the v2 design; ADR-0010 is the authoritative v1
> decision.

## Context

The slim MES wedge (per ADR-0001) maps a single Sparkplug metric threshold
crossing to a Progress event creation. The user has confirmed the v1 demo
fires `IssueCreatedEvent` with the issue linked to a static demo work order
and phase. This ADR specifies the YAML config file shape, the supported
operator set, the firing semantics, and the failure modes that S1 and S3
implement against.

A full binding engine (hot-reload, debounce, circuit breaker, multiple
operators, multiple targets, source-cycle protection, GUI panel, etc.) is
explicitly out of scope for v1 demo. Those live in `REQUIREMENTS.md`'s
post-demo section. This ADR captures the minimum surface that satisfies the
demo narrative without painting v2 into a corner.

## Decision

### File location and load behaviour

The bridge loads `/etc/progress-sparkplug/bindings.yaml` (mounted via
docker-compose volume) at process start. The file is parsed once with
Pydantic v2; any validation failure refuses bridge startup with a clear log.
There is **no hot-reload** in v1; changing the file requires a bridge
restart.

If the file is missing or empty, the bridge starts with no bindings active
and logs a single info-level line. This is the demo's emergency stop
(`make demo-stop-bindings` rewrites the file as `bindings: []` and restarts
the bridge container — no code path needed for disabling).

### Schema

```yaml
# /etc/progress-sparkplug/bindings.yaml

schema_version: 1

bindings:
  - name: pump3-vibration-anomaly
    enabled: true
    match:
      group: plant1
      edge: edge1
      device: pump3
      metric: Vibration
    when:
      operator: ">"            # ">" | "<" | ">=" | "<="
      threshold: 100
      latch_for_seconds: 60    # min time between fires of this binding
    fire:
      target: issue_created
      payload:
        title: "Pump 3 vibration anomaly: {value:.1f} mm/s"
        severity: warning
        linked_to:
          - { type: work_order, key: "{config.demo_wo_key}" }
          - { type: phase, key: "{config.demo_phase_key}" }

config:
  demo_wo_key: "WO-DEMO-001"
  demo_phase_key: "PH-DEMO-001"
  service_user_key: "USR-SPARKPLUG-BRIDGE"
  api_token_secret_path: "/run/secrets/progress_sparkplug_token"
  api_base_url: "http://api:8000/api"
```

### Field semantics

- `schema_version`: integer. Bridge refuses files whose schema_version does
  not match its compiled-in expectation.
- `bindings`: list. v1 demo expects exactly one binding entry; the bridge
  accepts more but doesn't optimize for many.
- `bindings[].name`: stable identifier used in logs, in the
  `source_metric` field on emitted events, and as the latching key.
- `bindings[].enabled`: boolean. False is equivalent to omitting the entry.
- `bindings[].match`: every field is required. Bridge matches against the
  decoded payload of `progress.sparkplug.*.metric.*.data` subjects. No
  wildcards, no patterns; a binding targets exactly one metric.
- `bindings[].when.operator`: one of `">"`, `"<"`, `">="`, `"<="`. No
  compound conditions, no equality, no rate-of-change in v1.
- `bindings[].when.threshold`: numeric. Compared against the metric's
  `value` field after Pydantic-validating the value to float.
- `bindings[].when.latch_for_seconds`: integer. After a fire, subsequent
  matches are suppressed for this many seconds. This is the only firing-rate
  protection in v1; it replaces the deferred debounce + circuit breaker.
  Default 60 if omitted.
- `bindings[].fire.target`: one of `"issue_created"`, `"batch_completed"`.
  v1 demo ships only `issue_created`; `batch_completed` is the stretch goal.
- `bindings[].fire.payload`: per-target payload template. String values
  support Python `str.format`-style interpolation against a small variable
  set (see below). Non-string values pass through.
- `config.demo_wo_key`, `config.demo_phase_key`: keys of the demo work order
  and phase that the restored DB ships (see ADR-0007 simulator scenario for
  rationale). Substituted into payload templates.
- `config.service_user_key`: ArangoDB key of the bridge's service user.
  Bridge does not need this directly; it's documented for ops.
- `config.api_token_secret_path`: path inside the bridge container where the
  Bearer JWT lives (Docker secret). Bridge reads once at startup; rotation
  requires restart in v1.
- `config.api_base_url`: where the bridge POSTs `/event`.

### Template variables available in `fire.payload`

```
{value}              # the metric's numeric value at fire time
{value:.1f}          # any Python format spec works
{group}              # e.g. plant1
{edge}               # e.g. edge1
{device}             # e.g. pump3
{metric}             # e.g. Vibration
{ts_utc_iso}         # ISO 8601 UTC timestamp at fire time
{config.<name>}      # any key from the top-level config block
```

Anything else raises a Pydantic-time validation error during file load.

### Firing semantics

1. Bridge subscribes to `progress.sparkplug.>` and decodes inbound payloads.
2. For each `metric.data` payload, the bridge walks the binding list. For
   each binding whose `match` block matches the payload's group/edge/device/
   metric tuple, the bridge evaluates `when`.
3. If `when` is true and the binding is not currently latched, the bridge:
   a. renders the `fire.payload` template;
   b. POSTs to `{api_base_url}/event` with body
      `{event_type: "ISSUE_CREATED", info: { issue_data: <rendered payload> }, source_metric: "<binding name>"}`
      and `Authorization: Bearer <token>`;
   c. logs the firing with binding name, value, and HTTP response;
   d. publishes a `progress.notification.sparkplug` notification with
      `kind: "binding.fired"`;
   e. starts a `latch_for_seconds` cool-down for that binding name.
4. If the API returns non-2xx, the bridge logs the response and does NOT
   retry in v1. The demo accepts that any failure is visible immediately;
   resilience features are deferred.
5. Bindings never re-enter via Sparkplug subjects (one-way flow). The
   `source_metric` field is included in the API call so any future audit
   layer can detect cycles.

### What v1 demo deliberately does NOT do

- No hot-reload of `bindings.yaml`. Restart bridge to change rules.
- No debounce window separate from the latch. Latch is the only suppression.
- No circuit breaker on N events / 60 s. The latch's lower bound is
  effectively the rate cap.
- No GUI to view or edit bindings. YAML on disk is the documented surface.
- No audit trail of evaluations that did not fire (only fires log).
- No multiple targets per fire. One target event type per binding.
- No retries on API failure. Surface the failure, accept the demo
  consequence.

These are all in `REQUIREMENTS.md` as deferred items.

## Trade-offs and rejected options

**Latching vs ISA-18.2 deadband + on/off delay.** ISA-18.2 is correct for
production alarm management but is two days of work. Single integer
`latch_for_seconds` with a clean reset on the next non-matching sample is
85% of the value at 10% of the cost.

**One target type vs polymorphic targets.** The Pydantic shape supports
multiple `target` values; v1 demo ships `issue_created` only. Adding
`batch_completed` is a stretch (per ADR-0001) and uses the same plumbing.

**`/api/sparkplug/signal` endpoint vs reusing `/api/event`.** Recon (ADR-0001
verified findings) confirmed that Progress already routes Prefect-flow
events through the generic `POST /api/event`. Adding a Sparkplug-specific
endpoint would duplicate machinery and bypass the existing audit path.
Bridge calls `/api/event` directly with `event_type: "ISSUE_CREATED"`.

**Templating engine choice.** Jinja2 was considered and rejected. Python
`str.format` covers the demo's variable interpolation needs and avoids
adding a templating dependency to the bridge.

## Consequences

- S1 (bridge) implements binding load + rule eval + HTTP POST exactly as
  spelled out here. No deviation without an updated ADR.
- S3 (slim wedge / simulator scenario) chooses the metric and threshold so
  that the simulator scenario triggers exactly one fire during the demo
  segment.
- S5 (demo data + restored DB) seeds:
  - the service user (`USR-SPARKPLUG-BRIDGE`) with appropriate scope on
    `event` creation;
  - a long-lived API JWT, mounted into the bridge container as a Docker
    secret;
  - the demo work order (`WO-DEMO-001`) and demo phase (`PH-DEMO-001`)
    referenced by the binding;
  - any other plumbing required for `IssueCreatedEvent` to apply cleanly
    against those keys.
- The `bindings.yaml` file lives next to the bridge service in
  `deploy/compose/sparkplug.yaml`'s mount layout (S1 owns the path).

## Related

- ADR-0001 — demo scope cut (which fixed Issue creation as the v1 wedge).
- ADR-0002 — NATS subject taxonomy (defines the payload shape this matches).
- ADR-0007 — simulator scenario (must produce one matching threshold cross).
- `backend/api/events/collaboration/issue_created.py` — target event class.
- `backend/api/utils/auth.py` — `issue_token()` for the service-user JWT.
