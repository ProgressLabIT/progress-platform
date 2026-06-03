# 0010 — Hardcoded Automation for v1 Demo (supersedes ADR-0003)

**Status:** decided
**Date:** 2026-04-28
**Audience:** S1 (bridge), S5 (demo data + walkthrough)
**Supersedes:** [ADR-0003](0003-bindings-yaml-schema.md) (which specified a YAML-driven binding engine)
**Related:** [ADR-0009](0009-stream-processing-framework.md) (the post-demo Bytewax plan that will replace this)

## Context

The May 15 demo's "MES wedge" is the moment when a Sparkplug metric drives
a Progress action — concretely, a metric crossing a threshold creates an
Issue in the Progress UI. ADR-0003 originally specified this as a
YAML-driven binding rule loaded by the bridge: schema, Pydantic loader,
generic-subject matching, dwell, latch, hot-reload, eventually a separate
`backend/bindings/` service.

Review on 2026-04-28 found that scope incompatible with the timeline. A
half-baked binding engine — a single rule, no UI panel, no proper
recovery, no hot-reload — would actually be **worse** for the demo
narrative than no engine at all: the audience are industrial integrators
who have seen real binding engines (Ignition, OAS, Litmus). A weak
implementation of a known-real category invites unfavourable comparison.

A simpler narrative serves the demo better: "we have a working
automation, here is the (short) Python code, the configurable engine
ships post-demo on top of Bytewax (ADR-0009)". This ADR captures that
decision.

## Decision

### Implementation shape

A single Python module:

```
backend/sparkplug_bridge/automations/__init__.py
backend/sparkplug_bridge/automations/pump_anomaly.py
```

Total budget: **~50–80 lines** of plain async Python. The file contains:

```python
"""
Hardcoded automation for the v1 demo: when pump3 vibration crosses 100 mm/s
for at least DWELL_SECONDS continuously, raise an Issue against WO-DEMO-001
and PH-DEMO-001 via POST /api/event.

This is a deliberately hardcoded implementation. The configurable, Bytewax-
driven binding engine is the v2 plan (see ADR-0009). When that ships, this
module is deleted.
"""

import os
import time
import httpx
import logging

log = logging.getLogger(__name__)

# Constants. NOT user-configurable in v1 demo. v2 reads these from bindings.yaml.
TARGET_METRIC_ID = "plant1.edge1.pump3.Vibration"
THRESHOLD = 100.0
DWELL_SECONDS = 5
LATCH_SECONDS = 60

LINKED_TO = [
    {"type": "work_order", "key": "WO-DEMO-001"},
    {"type": "phase",      "key": "PH-DEMO-001"},
]


class PumpAnomalyAutomation:
    def __init__(self, api_base_url: str, token_path: str):
        self.api_base_url = api_base_url
        self._token = self._read_token(token_path)
        self._first_violation_ts: float | None = None
        self._last_fired_ts: float = 0.0

    @staticmethod
    def _read_token(path: str) -> str:
        with open(path, "r") as f:
            return f.read().strip()

    async def on_metric_data(self, payload: dict) -> None:
        if not os.environ.get("SPARKPLUG_AUTOMATIONS_ENABLED", "true").lower() == "true":
            return
        metric_id = payload.get("metric_id") or _id_from_envelope(payload)
        if metric_id != TARGET_METRIC_ID:
            return

        value = payload.get("value")
        now = time.time()

        in_violation = isinstance(value, (int, float)) and value > THRESHOLD

        # Dwell tracking
        if not in_violation:
            self._first_violation_ts = None
            return
        if self._first_violation_ts is None:
            self._first_violation_ts = now
            return
        if now - self._first_violation_ts < DWELL_SECONDS:
            return

        # Latch tracking
        if now - self._last_fired_ts < LATCH_SECONDS:
            return

        await self._fire(payload)
        self._last_fired_ts = now
        self._first_violation_ts = None

    async def _fire(self, payload: dict) -> None:
        body = {
            "event_type": "ISSUE_CREATED",
            "info": {
                "issue_data": {
                    "title": f"Pump 3 vibration anomaly: {payload['value']:.1f} mm/s",
                    "severity": "warning",
                    "linked_to": LINKED_TO,
                }
            },
            "source_metric": "pump-anomaly-automation",
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(
                f"{self.api_base_url}/event",
                headers={"Authorization": f"Bearer {self._token}"},
                json=body,
            )
        if r.status_code >= 300:
            log.error("automation fire failed: status=%d body=%s", r.status_code, r.text)
        else:
            log.info("automation fired: created issue from %s = %s", TARGET_METRIC_ID, payload['value'])
```

The bridge's main loop calls `await pump_anomaly.on_metric_data(payload)`
on each decoded `metric.data` payload that arrives. Single instance,
single subscription, single fire path.

### What this gives the demo

- Vibration scenario in ADR-0007 produces a clean cross at t≈3:50.
- Five-second dwell suppresses the brief spike-then-back-down rejection.
- Sixty-second latch prevents re-fires while the alarm condition persists.
- POST to `/api/event` creates an Issue linked to the demo work order +
  phase; the audience sees it pop in the existing Progress UI within
  one second.
- Presenter can show the file (~75 lines) on screen during the demo to
  reinforce "no magic, just code".

### What this does NOT include

- No `bindings.yaml`, no Pydantic schema, no loader.
- No hot-reload (env-var emergency-disable is the only kill switch).
- No circuit breaker, no rate-limit guarding beyond the latch.
- No retry on API failure (the demo accepts immediate failure visibility).
- No multiple targets, no multiple operators, no other metrics.
- No separate `backend/bindings/` service; the automation is in-bridge.
- No machine-as-user resolution, no auto-link of running job, phase, WO,
  product, assignee chain. Hardcoded link list only.

All of these live in ADR-0009's v2 plan.

### Configuration knobs (v1 demo)

Configuration is via environment variables on the bridge container, NOT a
config file. The v1 surface is intentionally tiny:

| Env var | Default | Effect |
|---|---|---|
| `SPARKPLUG_AUTOMATIONS_ENABLED` | `true` | Set to `false` to disable all automations without a code change. Used by `make demo-stop-automations`. |
| `PROGRESS_API_BASE_URL` | `http://api:8000/api` | Where the automation POSTs. Can point to a remote API. |
| `PROGRESS_SPARKPLUG_TOKEN_PATH` | `/opt/progress/config/.sparkplug-token` | Path to the JWT bearer for the bridge's service user. |

Threshold, dwell, latch, target metric, and link list are in-code constants.
Changing them is a code change + redeploy.

### Token storage

The bridge reads its API JWT from a plain file at
`/opt/progress/config/.sparkplug-token` (file mode 0600), mounted into the
bridge container as a bind mount. This replaces the Docker-secret-based
proposal in the superseded ADR-0003.

Rationale: file management is simpler than Docker secret management for
this single token; if an attacker has filesystem access to
`/opt/progress/`, they have everything anyway, so the additional secret
abstraction adds operational complexity for no real security gain.

S5 ensures the token file is created during demo data setup (after
`progress restore` runs) and contains a JWT issued for the
`USR-SPARKPLUG-BRIDGE` service user with `production` or equivalent scope
for `/api/event` writes.

### Demo presentation notes

The presenter has the option to open the
`backend/sparkplug_bridge/automations/pump_anomaly.py` file in an editor
during the wedge segment of the demo (after the Issue appears). The file
fits on one screen at a comfortable webinar font size. Reading through
takes ~30 seconds. This is a deliberate transparency move:

> "Here is the automation that fired. Seventy-five lines of Python, one
> subscriber, one threshold, one rule. We've designed a configurable
> engine on Bytewax for v2 — it ships post-demo with YAML rules, hot
> reload, and a generic UNS subject reactor. For today's demo, this is
> the whole thing."

Whether to open the file on stage is a rehearsal-time call. The wedge
moment lands either way.

### Emergency stop

> **Amended 2026-05-11** — the original Makefile wrapper was dropped as
> bloat post-execution. Two defects surfaced when the wrapper was first
> exercised end-to-end (Phase 5 UAT walk): (1) `docker compose restart`
> does NOT re-read `environment:` from the yaml, so flipping the env var
> and running the Makefile target left the old value in effect; (2) the
> wrapper's inner `docker compose exec` wrote a file the bridge never
> read. The wrapper added zero value (it wrapped a single restart command)
> while implying an operator/maintainer role that doesn't exist on this
> solo-maintainer project.
>
> The kill switch is now one of:
>
> 1. Stop the `sparkplug_bridge` container via Docker Desktop (or
>    `docker stop progress-sparkplug_bridge-1`). The Phase 5 automation
>    is off because no bridge is running.
> 2. Edit `deploy/compose/.env`, set `SPARKPLUG_AUTOMATIONS_ENABLED=false`,
>    then `docker compose -f deploy/compose/sparkplug.yaml up -d --force-recreate sparkplug_bridge`.
>    The `--force-recreate` is required (plain `restart` keeps the old env).
>
> Original sketch (no longer in the tree, retained for ADR fidelity):
>
> ```make
> demo-stop-automations:
> 	docker compose exec sparkplug_bridge sh -c \
> 	  'echo SPARKPLUG_AUTOMATIONS_ENABLED=false > /tmp/automation.env'
> 	docker compose restart sparkplug_bridge
> ```

## Trade-offs and rejected options

**Ship a partial YAML engine anyway.** Rejected as discussed in Context.
A weak engine reads worse than an honest hardcode for this audience.

**Build the proper engine in 11 days.** Considered. With Bytewax adoption
+ separate-service architecture + bindings.yaml validation + dwell/latch
state machine + integration testing, the honest estimate is 4–6 days
inside the demo window. That's 50% of S3's parallel budget consumed by
v2-quality work the demo doesn't need. Rejected.

**Embed the YAML schema but only support the literal `pump_anomaly`
case.** Considered as a "schema-shaped hardcode". Rejected; the loader,
validator, and template engine are most of the work, and shipping them
unused is the worst of both worlds.

**Token in Docker secret instead of file.** Reverted to file per the
2026-04-28 review. Docker secrets add an abstraction that doesn't pay off
for one bridge with one token in this deployment model.

## Consequences

- S1 (bridge) implements the automation module per the code sketch above.
  S1 OR S3 owns the testing — likely S1 since the module lives inside the
  bridge.
- S3's original "slim wedge" scope (per ADR-0001) is reduced to:
  (a) tuning the simulator scenario in ADR-0007 to produce one clean
  cross during the demo segment, and (b) integration-testing that the
  automation fires and the Issue appears. ~1 day instead of 1.75.
- S5 ensures the restored DB has `WO-DEMO-001`, `PH-DEMO-001`, the
  `USR-SPARKPLUG-BRIDGE` user, and a long-lived JWT for that user written
  to `/opt/progress/config/.sparkplug-token`.
- The Phase 5 (Wedge) section of `ROADMAP.md` collapses from a multi-step
  wedge plan to a single-step automation phase.
- `REQUIREMENTS.md` v1 (Demo) WEDGE-DEMO-* requirements are revised to
  match this hardcoded shape; the broader binding-engine requirements
  move to Post-Demo (BIND-ENGINE-*).
- Total scope savings vs the original slim-wedge plan: ~1 day of S3
  work; another ~1 day of architectural-rework risk avoided.

## Related

- ADR-0001 — demo scope cut. Updated to reflect the hardcoded automation.
- ADR-0003 — superseded YAML schema; preserved for v2 design starting
  point.
- ADR-0007 — simulator scenario; the threshold (100), dwell (5s), and
  latch (60s) values match the in-code constants here.
- ADR-0009 — Bytewax post-demo plan; the engine that replaces this
  module.
- `backend/api/events/collaboration/issue_created.py` — target event
  class.
- `backend/api/utils/auth.py` — `issue_token()` for the service-user JWT.
- `backend/workflow/flows/flowcode/pause_offline_jobs.py` — Prefect-flow
  precedent for the same `POST /api/event` pattern.
