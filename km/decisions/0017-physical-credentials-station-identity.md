# 0017 — Physical credentials & station device identity (card-as-key, step-up, installed station builds)

**Status:** discussion
**Date:** 2026-06-17
**Audience:** security / ux (physical authentication layer for station login)
**Related:**
- Design discussion, 2026-06-16/17 session (reactive apps + physical-event login)
- [ADR-0015](0015-device-consumer-identity-model.md) — the device/operator session model and `DEVICE` identity this layer feeds
- [ADR-0016](0016-reactive-event-automation-contract.md) — the `route.command` reaction the verified login triggers
- [`km/security/nats-nkey-auth.md`](../security/nats-nkey-auth.md) §3 — the NKey nonce-challenge handshake this mirrors

## Context

For NFC/biometric station login, two questions must be answered: how does a badge *prove* identity (not merely assert it), and how does a Vue/Quasar SPA running in a browser identify itself as a *specific station/device*?

An NFC UID is an identifier, not a secret — single-factor and clonable. A naive "publish the UID, subscriber logs the user in" trusts a spoofable claim. And a generic browser tab is a poor anchor for a long-lived device identity.

## Decision

1. **Card-as-key, not card-as-token.** The badge credential must be an **asymmetric keypair in a secure element** (JavaCard / PIV / FIDO-class, ECC) that signs a server-issued nonce — the faithful NKey analog: the backend stores **only the public key** (store-no-secret, `nats-nkey-auth.md:20`). The tap becomes the NATS connect-handshake shape at the app layer:
   `backend nonce → card signs → reader relays { card_pubkey, nonce, ts, sig } over NATS → backend verifies vs registry`.
   The **reader stays dumb** — it holds no secrets and only relays, so a compromised reader can replay (defeated by the nonce) but cannot mint identities. A **static JWT written to card memory** (NTAG) is **rejected**: it is a clonable bearer token, no better than the UID against skimming. (DESFire/AES challenge-response is a cheaper middle option but symmetric — the backend holds a shared secret — and is a weaker analog.)

2. **Credential layering.** Reader = `DEVICE` credential (ADR-0015); card = the **USER's possession credential** carried over it; the backend mints the **USER session** on success. NFC alone is single-factor → **privileged actions step up** with a second factor (**PIN recommended**).

3. **Biometric is the inherence factor, deprioritized on GDPR grounds.** "The biometric *is* the token," but biometric templates are GDPR special-category data (storage, consent, liveness). Default to **NFC + PIN** (two factors, no biometric stored); use biometric only where a customer or regulation demands it.

4. **Only installed station builds are "devices"; casual tabs are plain USER sessions.** A browser tab is a poor trust anchor (`localStorage`/IndexedDB is clearable, XSS-exfiltratable, unpinned). Station mode runs an **installed build** (Capacitor / Electron / PWA — same Quasar codebase) holding the device token in **OS secure storage**. A casual browser tab needs no device identity and authenticates as `USER` normally. This single distinction dissolves most of the browser-identity problem.

5. **Auto-update is strongly recommended for kiosk/Capacitor mode.** Installed station builds otherwise become a per-station manual-rebuild maintenance trap. Ship an OTA / live-update channel for kiosk/Capacitor so stations self-update without hand-touching each box.

## Alternatives Considered

- **Static JWT on NTAG card memory.** Rejected — clonable bearer token (Decision §1).
- **DESFire EV3 / AES symmetric challenge-response.** Noted as a cheaper option but weaker (shared secret, server-side secret exists) — not the store-nothing NKey property.
- **Per-tab / `localStorage` device identity in a bare browser.** Rejected as the primary model — fragile and insecure. Retained only as a fallback for stations that must stay plain-browser, alongside mTLS client certificates (stronger but clunkier provisioning + proxy-side termination).
- **Biometric-first login.** Deprioritized — GDPR cost without offsetting need for most stations.

## Risks and Implications

- **Secure-element cards cost more and need personalization** (card generates its keypair, enrollment registers the pubkey). Budget for card hardware + a personalization step.
- **Badge theft still works** — possession is inherently stealable. Mitigations: revocation (kill the pubkey in the registry) and step-up (PIN) for privileged actions. The card-as-key model defeats *cloning/skimming and replay*, not theft.
- **Capacitor maintenance burden** is real; the auto-update mandate (Decision §5) is the mitigation, not an optional nicety.
- **Open:** primary station app target — warehouse (already Capacitor, easy) vs the main desktop SPA (needs an Electron/PWA station build or an mTLS cert). To be pinned before implementation.
