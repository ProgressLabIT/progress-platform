# 0015 — Device & consumer identity model (unified registry, dual credentials)

**Status:** discussion
**Date:** 2026-06-17
**Audience:** security / identity (cross-cutting — auth contract inherited by every worktree)
**Related:**
- Design discussion, 2026-06-16/17 session (reactive apps + physical-event login)
- [`km/security/tokens.md`](../security/tokens.md) — the Progress-API JWT (`ConsumerType`, `Token` collection, revocation)
- [`km/security/nats-nkey-auth.md`](../security/nats-nkey-auth.md) — decentralized NATS NKey/JWT auth + the enrollment service this ADR reuses
- [ADR-0002](0002-nats-subject-taxonomy.md) — subject taxonomy the device NATS permissions are scoped over
- [ADR-0016](0016-reactive-event-automation-contract.md), [ADR-0017](0017-physical-credentials-station-identity.md) — the contract and physical layer that consume this identity

## Context

NFC/biometric station login and IIoT edge nodes both need a **non-human identity**. Two authentication systems already exist and are deliberately separate (each cross-references the other as "not the same"):

- **Progress-API plane** (`tokens.md`): HS256 JWT + a `Token` collection record for stateful revocation. Identity = `consumer_key` + `ConsumerType` (claim `ctyp`); authz = `scope` + `context`, validated against the DB on each request.
- **NATS plane** (`nats-nkey-auth.md`): Ed25519 NKey + an account-signed user JWT; authz = pub/sub allow-list **baked into the JWT claims**, enforced offline by the server with no DB on the hot path.

The question: can one "device token" serve both — and should it conflate with the NATS permissioning system? A device must be able to talk to the API (establish a station/device session, open SSE) *and* to NATS (publish its channel), without standing up a third parallel identity system.

`ConsumerType` today is `{ USER, PROGRESS_APP='app', EQUIPMENT='equipment' }`. A grep confirmed `PROGRESS_APP` and `EQUIPMENT` have **zero live references** beyond the enum definition (`backend/api/models/auth.py:13-14`); only `ConsumerType.USER` is used. Equipment/Asset/Device are stated-but-unimplemented domain concepts, so renaming carries **no data migration**.

## Decision

**Unify the identity; keep the two enforcement planes separate.** The device *registry* conflates; the credentials and their enforcement do not.

1. **One Device registry = single source of truth.** A `Device` record carries `device_id`, `type`, `status`, station/owner binding, and a role. The **existing NATS enrollment service** (`nats-nkey-auth.md` §5/§6 "issue a device") becomes the single front door: one enrollment provisions **both** credentials, **per capability**:
   - a **NATS user JWT** (facility signing key, pub/sub allow-list per device type) — for devices that talk NATS;
   - a **Progress-API device token** (`ConsumerType.DEVICE`, HS256 + `Token` record) — for devices that hit the API / open SSE.
   A device gets only the credentials its type needs (NFC reader → NATS-only; kiosk → API-only; IIoT bridge → both). One `device_id` correlates the two for audit; one "disable device" fans out to both planes.

2. **Identity unified, enforcement not.** NATS enforces subjects from the signed JWT claims (offline, no DB on the hot path); the API enforces capabilities from `Token` + `scope`. We do **not** route NATS authz through the `Token` collection — that would put FastAPI in the connection hot path and destroy NATS's decentralized enforcement. The registry *generates* the NATS permission block; NATS still *enforces* it.

3. **`ConsumerType` refactor → `{ PROGRESS, DEVICE, 3PSW, USER }`.** No migration (members unused):
   - `PROGRESS` (was `PROGRESS_APP='app'`) — trusted first-party services + IIoT bridges (broad pub/sub).
   - `DEVICE` (replaces `EQUIPMENT='equipment'`) — constrained edge identity (own-channel only; see ADR-0016).
   - `3PSW` — third-party software (ERP, external plugins, integrations); distinct trust posture and lifecycle from our own devices.
   - `USER` — humans.

4. **Flat device scope.** The API device token carries a flat `scope` field. Per-device permissions live in the NATS user JWT's subject allow-list, pinned to `device_id`. **Flat scope ≠ flat permissions** — they live in different planes.

5. **Device ≠ Asset (must be documented explicitly).** `DEVICE` is an auth/identity type ("a non-human thing holding a credential"); `Asset`/`AssetClass`/role is the OT *domain* model ("modeled equipment"). They are not 1:1 — a kiosk, bridge, or print service is a device but not an Asset; a passive sensor behind a bridge is an Asset that holds no credential. The registry **links a Device to an Asset when one exists**, but never requires it. Naming the scope `ASSET` is rejected precisely to avoid welding the credential to the domain model.

6. **Two-layer sessions.** Split identity into a **device session** (long-lived; the kiosk/station; the trust anchor that holds the SSE channel and persists across operator changes and browser refresh because the *backend* holds the `station ↔ active-operator` binding) and an **operator session** (short-lived overlay; who is at the station now, swapped in/out by badge events). The device token authenticates the device session; the operator session rides on top.

## Alternatives Considered

- **One literal token for both planes.** Rejected — structurally incompatible: Ed25519 NKey-signed vs HS256 shared-secret; offline-claims authz vs DB-backed revocation. NATS will not honor a FastAPI JWT and vice versa.
- **NATS auth callout (maximal conflation).** The device presents one credential; NATS forwards the connect request to a Progress auth service that synthesizes the NATS user JWT from the registry. Elegant — and it removes the "re-scope = re-mint + redeploy creds" pain (`nats-nkey-auth.md:254`) — but adds a connect-time dependency and a privileged always-on service. **Deferred**, not rejected: static-mint at enrollment is the default; auth callout is the documented upgrade for when re-scope churn justifies it. Solo-ops + modest device count favors static-mint now.
- **Name the scope `ASSET`.** Rejected — see Decision §5.
- **Per-tab browser device identity.** Rejected; see ADR-0017.

## Risks and Implications

- **Revocation RTO asymmetry:** the API device token dies instantly (flip `revoked` on the `Token` doc); the NATS credential lags by the resolver `interval` (`nsc revoke` + push). Document the gap; for high-assurance kills, also drop the device's leaf/connection.
- **Timing is favorable, not free:** decentralized NATS auth is the *target* model and not yet wired into the live stack (`nats-nkey-auth.md:11`). Build the registry-as-single-front-door now so it is not a retrofit later.
- **Seed custody:** adopt `nats-nkey-auth.md` §7.1 from day one — the device generates its own NKey seed locally and ships only the public key; the enrollment service mints a JWT binding that pubkey and never sees the private seed.
- **The enrollment service holds the account signing key** — it is a privileged component (same property the §7 design already carries); guard it accordingly.
- **Open:** exact `3PSW` permission posture (tighter than `DEVICE`? sandboxed?) to be specified when the first external integration lands.
