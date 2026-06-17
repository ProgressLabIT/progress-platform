# 0016 — Reactive event/automation contract (device channels, subscriber-validated side effects, standard services)

**Status:** discussion
**Date:** 2026-06-17
**Audience:** architecture / protocol (extends ADR-0002; governs how physical/user events drive app reactions)
**Related:**
- Design discussion, 2026-06-16/17 session (reactive apps + physical-event login)
- [ADR-0002](0002-nats-subject-taxonomy.md) — the subject taxonomy these device channels extend
- [ADR-0015](0015-device-consumer-identity-model.md) — the `DEVICE` identity whose channels this contract scopes
- [ADR-0017](0017-physical-credentials-station-identity.md) — the physical credential layer for the login use case
- [`km/security/iiot-security.md`](../security/iiot-security.md) §3.3 — "tightest possible grant" ACL intent

## Context

Two desired capabilities are the same primitive pointed in opposite directions:

- **Inbound** — a physical event drives an app reaction (badge/scan → route a screen, inject data into a JobStep or BoM serials).
- **Outbound** — a user action (a job-step "action button") publishes context downstream, where other apps/plugins react.

Both are `(event source) → NATS subject → subscriber → effect`. The Sparkplug threshold → Issue automation already ships exactly this shape. This ADR fixes the contract: how `DEVICE` clients publish, how reactions are produced and authorized, and where that logic is allowed to live.

## Decision

1. **Events route through the backend; NATS is transport, not source of truth.** Physical/user events become **recorded Events** in the backend; NATS carries emission and downstream fan-out. Server→app reactions ride the **existing per-tab SSE channel** — the browser does **not** subscribe to NATS directly. Direct browser NATS-WS is reserved for high-frequency *read-only* telemetry only (e.g. the mill-twin HMI).

2. **`DEVICE` channel grant: own report channel (pub) + own command channel (sub), both pinned to `device_id`.** Least privilege — a compromised device can only pollute its own channel and can command nothing else. It is **not** literally publish-only: devices legitimately receive on their own command/desired channel (the bridge's `EDGE_DESIRED.<uuid>` subscription is the precedent, `nats-nkey-auth.md:94`). Side effects happen **downstream via subscribers** (plugins/apps), never by the device acting on others.

3. **Two channel classes — the channel proves origin, never payload truth.**
   - **Data channels** — trust-on-origin is acceptable (a sensor lying about a value is a data-quality problem).
   - **Inbound-context channels** — route-to-page and/or data injection (fill JobStep fields, BoM serials from machine data). The subscriber **must validate the claim/payload**, not trust it because it arrived on the right channel. NATS proves *which device* published; it does not prove the payload is true.

4. **Authz lives at the application level, in reviewed standard services with preset rule schemas.** Login and routing are **standard, reviewed services** — like user permissions, the *enforcement* is fixed code and config only toggles **data within a bounded vocabulary**. Configuration is a **closed schema** (select a vetted effect + parameters); it is **not** an embedded DSL or script. The moment config can express arbitrary logic, config *is* code and re-enters the review/test/version gate.

5. **Shared infra with custom plugins; trust boundary = code provenance.** Standard services and custom plugins subscribe over the same NATS + subscriber infrastructure — exactly as Prefect's system worker runs platform-provided and custom flows on the same execution infra. Platform-reviewed code is trusted; user-authored plugins are trust-tiered/sandboxed. Route **durable / multi-step** reactions to Prefect; keep **interactive** reactions as thin always-on subscribers.

6. **The reusable primitive: a `route.command` SSE message.** Carries `{ target, context, optional minted token }`. Login is `route.command → operator home` (carrying the freshly minted operator token); job-routing is `route.command → /work-session/{job}`. **Same mechanism, different trigger.** The handler lives at the **layout root (`App.vue` / `MainLayout.vue`)** so it can route anywhere from anywhere.

## Alternatives Considered

- **App-as-NATS-client (browser subscribes to NATS) as the default.** Rejected — a second realtime transport alongside SSE, a browser-resident NATS credential (extractable), and it bypasses event-sourcing. Kept only as the telemetry-only exception.
- **A generic configurable rules engine / open effect DSL.** Rejected — config-as-code becomes an unreviewed security surface, and it is overengineering for a solo maintainer. Custom plugins are the explicit escape hatch for user logic, at a lower trust tier.
- **Literal publish-only devices.** Rejected — devices need their own command/desired channel; "publish-only" would spawn an exception per device type.

## Risks and Implications

- **Interactive liveness:** fire-and-forget pub/sub hides failures from the publisher. Login/routing subscribers must be **durable JetStream consumers** (queue through a blip), with the SSE path back to the station as the user-facing feedback channel. Telemetry may drop; an interactive login may not.
- **Binding fragility:** the inbound flow hinges on `reader → station → kiosk` resolution in the registry. A stale binding routes a login to the *wrong screen* — a security event, not just a bug. This binding needs a real lifecycle, not a hand-edited config file.
- **Blast radius:** a compromised cheap device's reach = whatever the *most consequential subscriber* will do in response to its channel. Consequential subscribers must authorize the **triggering context**, not merely receive a message.
- **Config schema discipline:** the closed-schema boundary (Decision §4) is load-bearing; any drift toward an embedded DSL must trip the code-review gate.
- **Extends ADR-0002:** device-owned channel prefixes (report + command, derivable from `device_id`) and the inbound-context channel class need to be reflected in the subject taxonomy.
