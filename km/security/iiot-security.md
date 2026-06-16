# Progress Platform — IIoT Security Model

**Author:** CTO, Progress Platform
**Status:** v0.1 draft
**Last updated:** 2026-05-26
**Audience:** internal security reference + basis for prospect-facing security materials
**Companion documents:**
- `km/architecture/iiot-architecture.md` — IIoT architecture (topology, data plane, edge deployment, protocols, federation, HA). **The architecture half of this reference lives there.**
- `km/strategy/defense-aerospace-roadmap.md` — security & compliance posture roadmap (five cert-gated stages)
- `km/security/tokens.md` — current API token lifecycle (HS256 today; Ed25519 on roadmap)
- `km/security/nats-nkey-auth.md` — NATS NKey/JWT auth mechanism + operator bring-up runbook (the detail behind §5 and §3.3)
- `km/security/https.md` — Traefik / TLS termination and custom-cert handling
- `km/decisions/0011-database-substrate.md`
- `km/decisions/0012-graph-query-substrate.md`

---

## 1. Purpose & scope

This document owns the **security model** for the Progress Platform IIoT substrate: control-plane integrity, the signed-update supply chain, edge identity and PKI, the consolidated security posture, and the audit/compliance evidence story. It is the security companion to `km/architecture/iiot-architecture.md`, which owns topology, data plane, edge deployment topology, protocols, federation, and HA.

The *staged roadmap* to reach a defense/aerospace posture (and the honest current-state gap analysis) is in `km/strategy/defense-aerospace-roadmap.md`. This document is the *target model*; the roadmap is the path and timeline to it.

---

## 2. Security design principles

The six platform design principles **[P1]–[P6]** are defined in `km/architecture/iiot-architecture.md` §2.4. Three of them are security-critical and are the foundation of everything below:

- **[P4] Outbound-only edge.** Edge IPCs never accept inbound from the IT-side network. All ingress to the Enterprise tier is outbound from the edge over WSS:443, TLS. The customer's firewall ACL collapses to two outbound lines (NATS + registry); there are no inbound ports to defend.
- **[P5] mTLS and decentralised JWT auth as defaults.** Every NATS, API, and service-to-service connection is mutually authenticated with cryptographic identities derived from a documented PKI (§5). Not optional, not "advanced configuration."
- **[P6] Signed, A/B, rolled-back-on-failure updates.** Every component is delivered as a Cosign-signed image, referenced by content digest, deployed into one of two slots, health-gated, and automatically reverted on probe failure. No `docker.sock` exposure to any container (§3).

---

## 3. Control plane — signed deployment manifests, content-addressed images

The edge runs immutable infrastructure. All configuration is baked into the image. To change behaviour: rebuild image, push to registry, update the deployment manifest in KV. No remote commands, no live config tuning, no diagnostic shells through the control plane. SSH access exists separately on the customer's VPN / jump-host channel, outside the IIoT control plane.

This stance is a security primitive **[P5, P6]**, not an operational accident. It is also a selling point — every configuration change produces a signed, traceable artifact, which is exactly what auditors want.

**Update model: signed manifest in KV + content-addressed image + Cosign verification + podman/systemd A/B slots.**

```
CI/CD writes signed deployment manifest into EDGE_DESIRED.{uuid}
   manifest = {
     image_digest: "sha256:abc...",            # content-addressed, not tag
     image_repository: "registry.example.com/progress/bridge",
     effective_from: 2026-05-23T10:00:00Z,
     minimum_version: "v1.4.0",                # downgrade protection
     issuer: "deployments.progress.example.com",
     signature: "ed25519:..."                  # signed offline
   }
        │
        ▼
Edge Update Agent KV watcher fires
        │
        ▼
Validate manifest:
  ├── parse strictly (memory-safe parser; reject malformed input early)
  ├── verify ed25519 signature against pinned deployment-signing public key
  ├── check minimum_version against currently active version (no downgrade)
  ├── check effective_from <= now (no replay of stale manifests)
  └── validate registry hostname against allowlist
        │  (any check fails → abort + log to EDGE_REPORTED.last_validation_failure)
        ▼
Pull image by digest (NOT tag) from registry over HTTPS
        │  (registry can only serve the exact bytes pinned by digest)
        ▼
Verify Cosign signature on image against pinned Cosign public key
        │  (verification failure → abort + report)
        ▼
Stage into inactive slot (slot B if A is active)
        │
        ▼
Pre-swap health probe for N minutes (default 5)
        │  (probe failure → abort + report; slot A remains active)
        ▼
Atomic systemd unit swap: deactivate slot A, activate slot B
        │
        ▼
Post-swap health probe for further N minutes
        │  (probe failure → automatic rollback to slot A)
        ▼
EDGE_REPORTED.{uuid} write (active_digest, health, swap_timestamp)
```

### 3.1 What it takes to compromise the edge through this control plane

Three independent compromises are required:

1. **Deployment-signing key** — offline, in HSM or sealed file with documented custody chain (see §5 and `defense-aerospace-roadmap.md`).
2. **Cosign signing key** — separate, also offline, separate custody.
3. **Registry write access** — to host the malicious image bytes.

Two-person integrity on either signing key raises this to four or five compromises with separation of duties. This is the same threshold that protects production OS update channels at major OS vendors.

### 3.2 Key properties of the validation pipeline

- **Content-addressed.** Image references in the manifest are SHA-256 digests, never tags. Registry becomes untrusted byte distribution; even a fully compromised registry can only serve the exact bytes the manifest already pinned.
- **No `docker.sock` exposure.** The Update Agent runs under a constrained systemd unit and invokes `podman` directly. No container has access to the container runtime control socket. **[P6]**
- **Strict, fuzzed parser.** The manifest parser is minimal and treated as a security-critical component — fuzzed continuously, audited every release. Manifest parser CVEs are the highest-severity incident class on the edge.
- **Downgrade protection.** A compromised manifest-signer cannot push an old, vulnerable-but-validly-signed image because `minimum_version` is enforced. (Eventually: chained-revocation list with explicit deny entries.)
- **Replay protection.** `effective_from` rejects stale manifests; combined with KV revision numbers, an attacker who captured an old manifest cannot replay it later.
- **Rollback writes `EDGE_REPORTED`, not `EDGE_DESIRED`.** Rollback never modifies the desired state, so the operations dashboard surfaces failures without ping-pong loops between Agent and CI.
- **Phased rollout enforced at the orchestrator.** CI writes manifests in cohorts (5% → 25% → 100%) with bake periods, jitter on edge watchers, and pull-through registry caches at regional and facility levels to avoid thundering herd.

### 3.3 NATS account permissions on the edge (the silent prerequisite)

The edge's NATS user has the tightest possible permission grant:

- *Subscribe* on `EDGE_DESIRED.{its-uuid}` only — no wildcards, no other subjects.
- *Publish* on `telemetry.{its-isa-95-path}.*`, `events.{...}`, `EDGE_REPORTED.{its-uuid}` only.
- *No* request/reply, *no* KV write outside its own `EDGE_REPORTED` entry.

An ACL slip here undoes the entire security model. This is verified on every deploy by an automated ACL-diff check and surfaced in the security ADR for the deployment. This is condition #1 of the single-host hardening checklist in `km/architecture/iiot-architecture.md` §3.3.1.

This update model supersedes the original spec's `docker.sock`-based Agent pattern outright. ADR documenting the design is pending; `km/operations/edge-ota.md` is the Stage 1 deliverable.

### 3.4 KV bucket governance

The data-plane KV buckets are defined in `km/architecture/iiot-architecture.md` §3.2. Their security governance:

- Bucket ACLs are enforced **per-NATS-account**. Edge accounts cannot write `EDGE_DESIRED`; CI accounts cannot write `EDGE_REPORTED`.
- ACL drift is itself an alert (`audit.*`).
- `EDGE_DESIRED` is CI-write / edge-read-only; `EDGE_REPORTED` is edge-write / CI-read-only. This closes the "edge can overwrite its own target" hole.
- `max_history` and replicas are configured per bucket per ADR-0011/0012.

---

## 4. Edge hardening checklist (security view)

The single-host reference deploy is defensible only if the five conditions in `km/architecture/iiot-architecture.md` §3.3.1 hold. Restated here as a security checklist with rationale:

| # | Control | Security rationale |
|---|---|---|
| 1 | Tightest-possible NATS ACL on the edge user (no wildcards, no request/reply) | An ACL slip undoes the whole control-plane model. **[P5]** Verified by automated ACL-diff on every deploy (§3.3). |
| 2 | Content-addressed images + signed manifest + Cosign verification against pinned keys | Closes supply-chain + registry-compromise vectors (§3). Registry is untrusted byte distribution. **[P6]** |
| 3 | Bridge is a pure NATS client — no listening sockets, OT-NIC-bound, dropped caps, read-only rootfs, non-root | Eliminates IT-side inbound attack surface on the bridge; constrains blast radius. **[P3]** |
| 4 | Network namespaces + `nft` firewall enforce OT/IT separation, verified at boot | Namespacing substitutes for physical separation only if the firewall enforces it. **[P3]** |
| 5 | Documented host kernel patch cadence (critical-CVE RTO: 7 days) | On a single host the kernel is the only boundary between OT and IT containers; kernel CVE handling is the top edge operational discipline. **[P6]** |

The dual-host and data-diode variants (`km/architecture/iiot-architecture.md` §3.3.2–3.3.3) add physical separation, dedicated inter-host VLAN + mTLS, and (for diodes) unidirectional transport for customers whose compliance posture requires hardware-level evidence.

---

## 5. Provisioning and identity

> The NKey/JWT mechanism behind this section (signing chain, connect handshake, ACL-as-JWT-claims) and the operator bring-up runbook (hub / edge leaf / clients, `nsc` issuance, revocation) live in [`nats-nkey-auth.md`](./nats-nkey-auth.md). This section owns the *identity hierarchy and enrollment policy*; that doc owns *how the identities are issued and wired*.

**Edge enrollment** (replaces the original spec's USB cloud-init):

1. Edge IPC is built and tested in a controlled staging facility.
2. A **bootstrap certificate** (short-lived, X.509) is installed on the IPC during staging. Bootstrap cert is issued by a customer-side or Progress-side intermediate CA, tracked in a chain-of-custody log.
3. At first boot in the destination facility, the Edge Update Agent uses the bootstrap cert to authenticate to the regional **enrollment service**.
4. Enrollment service verifies the bootstrap cert, looks up the device's expected identity, **and requires two-person approval** (an operator + an admin) in the Progress admin UI before issuing the device's permanent NATS NKEY/JWT.
5. The bootstrap cert is revoked after first successful enrollment; the device transitions to its permanent identity.

This closes the original spec's "USB = social engineering" hole.

**Identity hierarchy** (per `defense-aerospace-roadmap.md`):

- **Operator:** Progress Platform itself (the system integrator entity). Signing key offline; HSM target in Stage 3.
- **Account:** per-customer (e.g. `acme-aerospace`). Account-signing key stored offline on customer-side or Progress-managed; documented custody chain.
- **Account (sub):** per-facility, optionally. Allows facility-scoped JWT revocation without affecting other facilities.
- **User:** per-service-instance (e.g. `acme.vicenza.line3.bridge1`). Signed by the facility's Account key.

**Revocation:** documented procedure with RTO < 1 hour. Account JWT carries a `revocations` field maintained centrally. Revocation list propagation tested as part of DR drills. (Current API-token revocation mechanism: `km/security/tokens.md`.)

---

## 6. Security model summary

| Concern | Posture |
|---|---|
| **Transport** | mTLS end-to-end (NATS, API, DB, Prefect, internal HTTP). External edge: Traefik + Let's Encrypt or customer-CA-issued cert (see `km/security/https.md`). Internal: cert-manager + internal CA (offline root + online intermediate). |
| **Identity** | Decentralised NATS JWT (Operator → Account → User) + Progress-API JWT (Ed25519 post-Stage-1; HS256 today per `backend/api/utils/auth.py`, documented in `km/security/tokens.md`). |
| **Revocation** | NATS revocation lists + Progress `Token.revoked` collection. Documented RTO. |
| **Audit trail** | Event-sourced platform events (immutable in Postgres post-ADR-0011); structured audit events on NATS `audit.*`; `pgAudit` on the DB. NIST 800-171 AU-family coverage. |
| **Encryption at rest** | LUKS at host level; Postgres TDE (Cybertec / Percona) for customers requiring FIPS-validated modules in Stage 3. |
| **Supply chain** | Cosign-signed images; SBOM (syft) per image; signing key in sealed file (Stage 1) → HSM (Stage 3). SLSA L3 target in Stage 3. |
| **Vulnerability management** | Dependabot + Renovate + weekly image vuln scan; public CVD policy from Stage 2. |
| **Multi-tenancy isolation** | NATS account-level isolation between customers in Managed Cloud; documented pen-test scope from Stage 1. |

---

## 7. Audit & compliance evidence

| Standard | Control family | How Progress evidences it |
|---|---|---|
| **AS9100D 7.5** (documented information) | Records | Event store is the system of record; all events immutable, queryable, exportable |
| **AS9100D 8.5.2** (identification & traceability) | Genealogy | Serial graph (`contains` edges, see ADR-0011) + event history per serial = full as-built/as-maintained chain |
| **NIST 800-171 AU-2/AU-3** | Auditable events | `audit.*` NATS subjects + `pgAudit` + platform event store |
| **IEC 62443-3-3 SR 2.8** | Auditable events | Same as above |
| **NIS2 Article 21** | Incident handling | Incident response runbook (Stage 2) + audit-trail forensic preservation |
| **GDPR Art. 30** | Records of processing | Documented data classification + replication policy per `km/architecture/iiot-architecture.md` §3.5 |

A dedicated `km/compliance/matrix.md` (Stage 0 deliverable per defense roadmap) maps every applicable control to evidence pointers in the codebase / deployment.

The event-sourcing model is what makes the AS9100D 7.5 + 8.5.2 evidence story essentially free — every state-changing operation is captured as an immutable event before it becomes a state mutation, with the transaction guaranteeing both halves succeed or neither does.

---

## 8. Open questions / unresolved (security)

Security-specific open questions; the architecture set is in `km/architecture/iiot-architecture.md` §6.

1. **Edge OTA orchestrator implementation** — write our own thin updater on podman+systemd vs adopt Mender / RAUC. ADR pending; depends on Stage 1 spike. (Affects §3.)
2. **PKI substrate** — internal cert-manager + our CA vs customer-issued certs from their CA vs hybrid. Likely customer-driven per deployment. (Affects §5.)
3. **Live-config-without-redeploy workflow** — the immutable-infrastructure stance (§3) means every behaviour change requires a new signed image. This is a security feature but an operational tension for customers used to runtime config knobs. Resolution path: invest in a CI/CD pipeline that makes "change threshold → new image → new deploy" feel like 90 seconds end-to-end; document the workflow as a feature, not a limitation. Stage 2 deliverable. Where customers reject immutable infrastructure outright, document the trade-off frankly and let the customer choose — do not add a runtime-config back-channel that undermines the control-plane security model.

---

## 9. Reference list

**Internal:**
- `km/architecture/iiot-architecture.md` — IIoT architecture (topology, data plane, edge deployment, protocols, federation, HA)
- `km/strategy/defense-aerospace-roadmap.md` — security / compliance posture roadmap
- `km/security/https.md` — Traefik / TLS setup
- `km/security/tokens.md` — current API token lifecycle
- `km/security/nats-nkey-auth.md` — NATS NKey/JWT auth mechanism + operator bring-up runbook
- `km/architecture/sparkplug.md` — Sparkplug B integration details
- `km/decisions/0002-nats-subject-taxonomy.md`
- `km/decisions/0008-natsmqtt-subject-mapping.md`
- `km/decisions/0010-hardcoded-automation-for-v1-demo.md`
- `km/decisions/0011-database-substrate.md`
- `km/decisions/0012-graph-query-substrate.md`

**External standards:**
- IEC 62443-3-3 — System security requirements
- IEC 62443-4-1 / 4-2 — Secure development lifecycle / component security
- NIST SP 800-171 r3 — Protecting CUI in Nonfederal Systems
- DFARS 252.204-7012 / CMMC Level 2 — US defense flow-down
- NIS2 Directive (EU) — essential-entity cybersecurity obligations
- OPC-UA Part 2 — Security Model
- AS9100D — Quality Management Systems (aerospace)

---

## 10. Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 (split) | 2026-05-26 | CTO | Created by splitting `km/strategy/iiot-architecture.md`. Inherits the control plane (signed manifests, content-addressed images), edge NATS ACLs, provisioning/identity, security-model summary, and audit/compliance sections; architecture/topology content stays in the companion `km/architecture/iiot-architecture.md`. `tokens.md` and `https.md` relocated into `km/security/`. |
