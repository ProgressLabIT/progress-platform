# Station Login — Physical Credentials & Device Identity

**Status:** draft — design under discussion (see [ADR-0017](../decisions/0017-physical-credentials-station-identity.md))
**Date:** 2026-06-17
**Audience:** security — NFC/biometric station login and how a SPA identifies as a specific device
**Companion documents:**
- [ADR-0017](../decisions/0017-physical-credentials-station-identity.md) — the decision record this doc elaborates
- [ADR-0015](../decisions/0015-device-consumer-identity-model.md) — device/operator session model + `DEVICE` identity
- [ADR-0016](../decisions/0016-reactive-event-automation-contract.md) — the `route.command` reaction a verified login triggers
- [`nats-nkey-auth.md`](./nats-nkey-auth.md) §3 — the NKey nonce-challenge handshake this mirrors
- [`tokens.md`](./tokens.md) — the session token minted on success

> Forward-looking. Not implemented; contract in `discussion`.

## 1. Card-as-key, not card-as-token

The badge credential must be an **asymmetric keypair in a secure element** (JavaCard / PIV / FIDO-class, ECC) that signs a server-issued nonce — the NKey analog (the backend stores **only the public key**; store-no-secret). The tap reproduces the NATS connect handshake at the app layer:

```
backend nonce → card signs → reader relays { card_pubkey, nonce, ts, sig } over NATS → backend verifies vs registry
```

- **Reader stays dumb** — holds no secrets, only relays. A compromised reader can replay (defeated by the nonce) but cannot mint identities.
- **Rejected:** a static JWT written to card memory (NTAG) — a clonable bearer token, no better than the UID against skimming.
- **Weaker middle option:** DESFire / AES challenge-response — symmetric (the backend holds a shared secret), not the store-nothing property.

## 2. Credential layering

- Reader = `DEVICE` credential (ADR-0015).
- Card = the **USER's possession credential**, carried over the reader.
- On success the backend mints the **USER (operator) session** (ADR-0015; `tokens.md`) and pushes a `route.command` to the bound station (ADR-0016).

## 3. Factors

- NFC alone is single-factor (possession) → **privileged actions step up** with a second factor (**PIN recommended**).
- Biometric is the inherence factor ("the biometric *is* the token") but is **deprioritized on GDPR grounds** (templates = special-category data: storage, consent, liveness). Default **NFC + PIN**; use biometric only where a customer or regulation demands it.

## 4. Station device identity

Only **installed station builds are "devices"**; casual browser tabs are plain `USER` sessions needing no device identity (a tab is a poor trust anchor — `localStorage` is clearable, XSS-exfiltratable, unpinned).

- **Station mode** = an installed build (Capacitor / Electron / PWA, same Quasar codebase) holding the device token in **OS secure storage**.
- **Auto-update is strongly recommended** for kiosk/Capacitor mode (OTA / live-update) — otherwise stations become a per-box manual-rebuild maintenance trap. This is a mitigation, not a nicety.
- **Fallbacks** for stations that must stay plain-browser: an mTLS client certificate (stronger, clunkier provisioning + proxy-side termination) or an enrollment-ceremony → IndexedDB token (fragile).

## 5. Risks

- Secure-element cards cost more and need personalization (the card generates its keypair; enrollment registers the public key).
- Badge theft still works (possession is stealable) — mitigated by revocation + PIN step-up. Card-as-key defeats cloning/skimming/replay, not theft.
- **Open:** primary station app target — warehouse (already Capacitor, easy) vs the main desktop SPA (needs an Electron/PWA station build or an mTLS cert).
