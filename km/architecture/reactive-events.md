# Reactive Events & Automation Contract

**Status:** draft — design under discussion (see [ADR-0016](../decisions/0016-reactive-event-automation-contract.md))
**Date:** 2026-06-17
**Audience:** architecture — how physical/user events drive app reactions and downstream automation
**Companion documents:**
- [ADR-0016](../decisions/0016-reactive-event-automation-contract.md) — the decision record this doc elaborates
- [ADR-0015](../decisions/0015-device-consumer-identity-model.md) — device/consumer identity the channels are scoped to
- [ADR-0017](../decisions/0017-physical-credentials-station-identity.md) — physical credentials for the login use case
- [`../decisions/0002-nats-subject-taxonomy.md`](../decisions/0002-nats-subject-taxonomy.md) — subject taxonomy these channels extend
- [`../security/tokens.md`](../security/tokens.md) — SSE tickets / session tokens used on the response path

> Forward-looking. None of this is implemented yet; the contract is in `discussion`. It describes the target shape so the device-identity, login, and routing workstreams build against one model.

## 1. The primitive

Everything here is one shape pointed two ways:

`(event source) → NATS subject → subscriber → effect`

- **Inbound:** a physical event drives an app reaction (badge/scan → route a screen; machine data → fill JobStep fields or BoM serials).
- **Outbound:** a user action (a job-step "action button") publishes context downstream, where other apps/plugins react.

The Sparkplug threshold → Issue automation already ships this shape; this contract generalizes it.

## 2. Events route through the backend; NATS is transport

Physical/user events become **recorded Events** in the backend (event-sourcing stays the source of truth); NATS carries emission and fan-out. Server→app reactions ride the **existing per-tab SSE channel** — the browser does **not** subscribe to NATS directly. Direct browser NATS-WS is reserved for high-frequency *read-only* telemetry (e.g. the mill-twin HMI), never for control or identity.

Rationale: a second browser realtime transport means a browser-resident NATS credential (extractable) and bypasses the event log. SSE rides the existing session/ticket auth (`../security/tokens.md`).

## 3. Device channel grant

A `DEVICE`-scoped client (ADR-0015) may:

- **publish** its own report channel, and
- **subscribe** its own command channel,

both pinned to `device_id`. Least privilege — a compromised device pollutes only its own channel and commands nothing else. (Not literally publish-only: the bridge's `EDGE_DESIRED.<uuid>` subscription is the precedent.) Side effects happen downstream via subscribers, never by the device acting on others. Channel prefixes extend the ADR-0002 taxonomy and must be mechanically derivable from `device_id`.

## 4. Two channel classes — channel proves origin, not payload truth

NATS proves *which device* published; it never proves the payload is true.

- **Data channels** — trust-on-origin acceptable (a sensor lying about a value is a data-quality problem).
- **Inbound-context channels** — route-to-page and/or data injection (JobStep fields, BoM serials from machine data). The subscriber **must validate the claim/payload**, not trust it because it arrived on the right channel.

This is the security crux: identity and consequential triggers are channel-class *inbound-context*, and the subscriber owns validation + authz of the triggering context.

## 5. Where the logic lives: standard services vs custom plugins

- **Login and routing are standard, reviewed services** with preset rule *schemas*. Like user permissions: enforcement is fixed code; config only toggles **data within a bounded vocabulary**. Configuration is a **closed schema** (pick a vetted effect + parameters) — never an embedded DSL or script. The moment config expresses arbitrary logic, config *is* code and re-enters the review gate.
- **Custom plugins** are the explicit escape hatch for user-authored logic, at a lower trust tier (sandboxed).
- Trust boundary = **code provenance**, exactly as Prefect's system worker runs platform-provided and custom flows on the same execution infra. Route durable / multi-step reactions to Prefect; keep interactive reactions as thin always-on subscribers.

## 6. The `route.command` SSE primitive

The reusable server→app message:

```jsonc
{
  "type": "route.command",
  "target": "/work-session/{job}",   // or "/home"
  "context": { /* job, station, injected fields … */ },
  "session": "<minted token>"        // optional, e.g. on a login grant
}
```

- Login = `route.command → operator home` (carrying the freshly minted operator token).
- Job-routing = `route.command → /work-session/{job}`.

Same mechanism, different trigger. The handler lives at the **layout root (`App.vue` / `MainLayout.vue`)** so it can route anywhere from anywhere.

## 7. Risks

- **Interactive liveness:** login/routing subscribers must be durable JetStream consumers; fire-and-forget hides failures from the publisher. The SSE path back to the station is the user-facing feedback channel.
- **Binding fragility:** `reader → station → kiosk` resolution lives in the device registry; a stale binding routes a login to the wrong screen — a security event. Needs a real lifecycle.
- **Blast radius:** a compromised device's reach = whatever the most consequential subscriber does in response. Consequential subscribers must authorize the triggering context.
