---
slug: wire-nats-nkey-auth-xref
status: complete
branch: DEV
committed: true
---

# Summary — Wire cross-link to km/security/nats-nkey-auth.md

Made the new NATS NKey/JWT auth note discoverable from the IIoT security model doc.
The note itself was authored in the same session (NKey/JWT mechanism deep-dive +
operator bring-up runbook); this task wires it in.

## Changed
- `km/security/iiot-security.md`:
  - Companion-documents list (top): added `nats-nkey-auth.md` line.
  - §5 (Provisioning and identity): added a blockquote pointer delineating ownership
    — §5 owns the *identity hierarchy + enrollment policy*; `nats-nkey-auth.md` owns
    *how identities are issued and wired* (signing chain, handshake, ACL claims, `nsc` runbook).
  - §9 (Reference list → Internal): added `nats-nkey-auth.md` entry.
- `km/security/nats-nkey-auth.md`: new note (authored earlier this session) — committed
  alongside the cross-links as one ship-grained docs unit.

## Committed
Atomic commit on DEV. Staged only the two `km/security/*.md` files. `.planning/`
excluded from DEV per the branching regime; this SUMMARY left untracked.

## Verified
- New note links back to `iiot-security.md` (§ companion list) — bidirectional.
- Three inbound references from `iiot-security.md` all resolve to `./nats-nkey-auth.md`.
