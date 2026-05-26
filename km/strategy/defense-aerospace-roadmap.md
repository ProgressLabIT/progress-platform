# Progress Platform — Defense/Aerospace Architecture Roadmap

**Author:** CTO, Progress Platform
**Status:** Internal strategy draft — prep document for upcoming prospect meeting (~2 weeks out)
**Frame:** Canadian HQ defense/aerospace group, serves DoD + NASA, EU VP is the lead contact
**Document version:** v0.1 — draft for review
**Last updated:** 2026-05-21

---

## Context

A large defense/aerospace prospect (Canadian HQ, US DoD + NASA contracts, EU VP lead) will engage in ~2 weeks. We need a credible roadmap showing how Progress Platform reaches the security and assurance posture they expect — for both **on-prem customer-controlled deployments** (the primary model) and our **internal Managed Cloud** (treated by analogy, not the focus of this doc).

This document reframes the earlier "SME-first" CTO roadmap (May 2026) against the actual customer profile we already serve: **AS9100D-certified discrete manufacturers**, expanding toward AS9100D customers in **regulated defense supply chains**. AS9100D itself is a quality-management standard with no cybersecurity clauses; what changes for defense is the **flow-down** from primes — NIST SP 800-171, DFARS 252.204-7012, CMMC Level 2 in the US; NIS2 + IEC 62443 in the EU; ITSG-33 and Controlled Goods Program (CGP) considerations in Canada.

The earlier roadmap deferred most hardening to "Stage 3" on the premise that solo-OSS-to-SME is the dominant path. That framing is wrong for this prospect. This rewrite shows a **shorter, more credible path** anchored to certification gates rather than commercial milestones, with HA explicitly modeled as **on-prem high-availability** (customer-deployed and customer-operated infrastructure).

---

## Honest current state (May 2026)

Documented for credibility — no embellishment. All claims traceable to file paths in this repository.

| Area | What exists today | Gap for defense |
|---|---|---|
| NATS transport | Plain TCP, no TLS; `deploy/config/nats-server.conf` has no `tls`, `authorization`, `accounts`, `operator` blocks | mTLS + decentralized auth required |
| NATS auth | None — `backend/api/utils/nats_client.py` connects without credentials | Operator/Account/User JWT chain needed |
| API auth | HS256 JWT with DB-backed revocation in `backend/api/utils/auth.py` (`issue_token` + `Token` collection with `revoked` flag); single active session per user | Solid base. Switch to asymmetric (RS256/Ed25519), add MFA, document revocation SLO |
| Bridge → API | Static file JWT at `/opt/progress/config/.sparkplug-token`, loaded once at startup per `backend/sparkplug_bridge/automations/pump_anomaly.py`, mode 0600 | No rotation/refresh, no key custody chain |
| Edge OTA | **Does not exist.** No docker-socket agent, no Gitea registry, no image-signing pipeline | Entirely greenfield — design from scratch, no legacy to migrate |
| NATS KV | Used only for Sparkplug session/alias/last-value state (`backend/sparkplug_bridge/kv_store.py`); 4 buckets, schema_version 1 | Foundation usable, but governance (ACL per bucket, immutable history) not configured |
| Secrets | Docker Swarm secrets + plaintext file fallback via pydantic-settings `secrets_dir`; no Vault | Acceptable for v1; defense deploys need HSM-backed Account signing keys |
| TLS at edge | Traefik + Let's Encrypt + optional custom-cert file provider (`km/architecture/https.md`) | External edge covered; internal mTLS missing |
| ArangoDB | `ARANGO_NO_AUTH=1` in `deploy/compose/dev.yaml` | Must verify prod compose never inherits this flag; recommend deny-by-default |
| Audit trail | Event-sourced — immutable `Event.save()` chain through ArangoDB transaction, 50+ event types | Strong base for NIST 800-171 AU family; needs documented retention + tamper-evidence |
| Threat model | Per-feature only, in some phase `PLAN.md` files; no platform-level model | Required deliverable for prospect |
| Compliance docs | Zero — no AS9100D, ITAR, NIST 800-171, CMMC, IEC 62443, NIS2 mentions anywhere in repo | Required deliverable for prospect |
| ADRs | 10 decided in `.planning/workstreams/sparkplug-demo/decisions/`; 0010 establishes bridge token pattern | Good governance pattern; extend with security-scoped ADRs |
| Code hygiene | 62 bare `except:` clauses, 44 stray `print()` calls per `.planning/codebase/CONCERNS.md` | Audit-trail concern (swallowed exceptions = missing audit events); cleanup is a Stage 1 line item |

**Key correction to the prior roadmap:** the prior version assumed "no auth/TLS today is acceptable for design partners." For a defense prospect that lens is wrong. NATS auth + mTLS becomes a **Stage 1 must-fix**, not a "Stage 2 foundation."

---

## Strategic reframe

The prior roadmap framed the product as solo-OSS-to-SME, with regulated-industry readiness as Stage 4 (2028+). The defense prospect changes three premises:

1. **Customer-operated on-prem is the default, not the fallback.** HA, DR, observability — all designed for a customer's IT/OT team to run on their own metal, behind their own firewall, with their own PKI. Our Managed Cloud uses the same primitives; we just operate them ourselves.
2. **AS9100D customer base is leverage, not a starting point.** We already pass AS9100D customer due diligence (quality system, traceability, configuration management). The delta to defense is **cybersecurity assurance**, which sits next to — not replacing — AS9100D.
3. **Cert ambition is dual-track:** Stage 1–2 is *deployment support* (we help the customer's certification — hardened reference deploys, threat models, audit evidence). Stage 3+ adds *product certification* (IEC 62443-4-1 process / 4-2 component) once a real customer commitment funds the cycle.

---

## Compliance frame (dual-track EU/NATO + US/Canada)

The prospect spans three regimes. The roadmap is structured so the same engineering work satisfies multiple frameworks; only the documentation/evidence layer forks.

| Regime | Primary controls | When it bites |
|---|---|---|
| **EU baseline** | NIS2 (essential-entity profile), IEC 62443-3-3 SL-1 → SL-2, EN 17640 / Common Criteria where relevant, GDPR for any operator-identifiable telemetry | EU VP is the entry point. Likely first deployment context. |
| **US flow-down** | NIST SP 800-171 r3, DFARS 252.204-7012, CMMC Level 2 (53 of 110 controls assessed), FIPS 140-3 validated crypto modules where CUI is touched | If parent group flows DoD-contract obligations to the deployment. Probable Stage 2. |
| **Canada** | ITSG-33 (CCCS), Controlled Goods Program if technical data is in scope, PROTECTED B handling if applicable | If HQ-controlled data crosses the deployment. Treat as Stage 2 alongside US. |
| **Cross-cutting** | NATO AQAP 2110/2210 (quality + software assurance), NATO STANAG 4427 (configuration management) | If NATO contracts in scope. Align AS9100D evidence to AQAP. |

Mapping note: a single ISO 27001 ISMS + a single secure-development lifecycle satisfies the *process* requirements of all four regimes. The *technical* controls (mTLS, MFA, audit logging, encryption-at-rest, key custody, vulnerability management) are also largely common. **Build once, document many.**

---

## Roadmap — five stages anchored to certification gates

Stages are gated by **assurance milestones**, not calendar dates. Each stage produces a tangible artifact the prospect can verify. Realistic durations shown for a solo-maintainer-plus-one-partner team; multiplied if scope or staffing changes.

### Stage 0 — Baseline credibility (now → 8 weeks)

**Purpose:** Walk into the prospect meeting with documents that prove the architecture has been thought through. No new product code required for the meeting itself; deliverables are documentary + a small number of must-fix configuration changes.

| Deliverable | Form | Effort |
|---|---|---|
| **Threat model v1** (STRIDE) | Markdown in `/km/security/threat-model.md`. Covers data plane (Bridge → NATS → API → DB) and control plane (KV-driven update model). Identifies STRIDE class per asset. | 1.5 wk |
| **Compliance matrix v1** | `/km/compliance/matrix.md`. Rows: NIST 800-171 r3 control families, IEC 62443-3-3 requirements, NIS2 articles. Columns: status (Implemented / Partial / Planned / N/A), evidence pointer, target stage. | 1 wk |
| **Reference secure deploy** | A new compose profile `deploy/compose/secure.yaml` that enables NATS TLS + JWT auth, removes `ARANGO_NO_AUTH`, forces Traefik to require client certs on admin paths, and sets explicit Docker user IDs. Documented in `km/operations/secure-deploy.md`. | 2 wk |
| **NATS auth chain (operator/account/user) — minimal** | One operator, per-customer account, per-service user. Issuance scripts in `deploy/scripts/nats-auth/`. Account-signing key stored offline, documented procedure. | 2 wk |
| **JWT-revocation SLO + key custody doc** | `/km/security/key-custody.md` — where each signing key lives, who has access, rotation cadence, revocation procedure with RTO. | 3 d |
| **AS9100D evidence alignment** | One-page mapping showing how existing event-sourcing audit trail satisfies AS9100D 7.5 (documented information) + 8.5.2 (identification & traceability), with pointer to corresponding IEC 62443 / NIST controls. | 2 d |
| **Architecture risk register** | `/km/security/risk-register.md` — top 20 risks, current mitigation, residual risk, owner. | 3 d |
| **Honest gap list** | `/km/security/gaps.md` — what we do NOT have and when we will. Defensive credibility move. | 2 d |

**Exit criterion:** A defense CISO can read these eight documents, understand exactly what we are and aren't, and have a credible roadmap to where we're going. Total: ~7–8 wks, fits the "ready before prospect conversation matures" window.

### Stage 1 — Pilot-ready hardening (~3 months after Stage 0)

**Purpose:** A customer can deploy Progress Platform on their own metal, in a controlled pilot (single line, non-CUI data initially), and pass an internal security review.

| Deliverable | Form | Notes |
|---|---|---|
| **End-to-end mTLS** | NATS, API, ArangoDB, Prefect, internal HTTP. Cert issuance via cert-manager + an internal CA (offline root, online intermediate). | Hardest cert-handling integration point is ArangoDB (`ARANGO_NO_AUTH=1` removal verification + client-cert auth). |
| **Asymmetric API tokens** | Replace HS256 with Ed25519. Reuse existing `Token` collection for revocation. JWKS endpoint for verifiers. | Migration script + dual-issuance window. |
| **Edge OTA — A/B with signed images** | Podman + systemd + Cosign verification + A/B unit slots + health-gated promotion + automatic rollback. **No `docker.sock` exposure to any container.** | Replaces the prior "highly privileged Docker socket Agent" design. ADR-0011 required. |
| **Cosign signing in Gitea Actions + deployment-manifest signing** | SBOM (syft) per image; Cosign-signed manifest; **separate** offline ed25519 deployment-signing key for the signed-manifest channel described in `km/strategy/iiot-architecture.md` §3.3. **Both keys HSM-backed from Stage 1** — these are the two cryptographic artifacts that the entire edge control-plane security model depends on; sealed-file custody is too weak given how load-bearing they are. Two-person integrity documented; YubiHSM2 acceptable at this stage, AWS CloudHSM / Thales reserved for Stage 3 Managed Cloud. | Single most-asked supply-chain question; closes the most concentrated attack surface in the architecture. |
| **KV split** | `EDGE_DESIRED` (CI write, edge read-only) + `EDGE_REPORTED` (edge write, CI read). ACLs per account. `max_history` and replicas configured. | Closes the "edge can overwrite its own target" hole. |
| **Centralized observability** | Prometheus + Loki + Grafana on-prem reference deploy. SLO doc + sample alert rules. | Customer's SOC integration via syslog/CEF forwarder. |
| **JetStream backpressure policy** | Per-stream `max_bytes`, `max_age`, `discard_policy`. Disk monitoring + KV-reported degradation. | Documented sizing model. |
| **OPC-UA SignAndEncrypt mandatory** | Config schema rejects `None` security mode at startup. | Pre-emptively closes Bucket A finding #3.5 from prior review. |
| **Code hygiene pass** | Eliminate the 62 bare `except:` and 44 `print()` sites flagged in `.planning/codebase/CONCERNS.md` — they are audit-trail risks (swallowed errors = missing events). | Mechanical but credibility-significant. |
| **Pen-test 1: focused** | 3-day engagement, scope = provisioning + KV ACL + account isolation. EU firm (e.g., Securify, SEC Consult, Yarix). Findings published to customer; P1/P2 closed. | First external proof point. |

**Exit criterion:** Pilot site running for 30+ days with one OTA cycle and one deliberate rollback drill verified. Customer security team has signed off on the threat model.

### Stage 2 — Production-ready, NIST 800-171 evidence-complete (~6 months after Stage 1)

**Purpose:** The pilot graduates to production. Customer's CMMC L2 or NIS2 audit can use Progress deployment as in-scope evidence without findings on our side.

| Deliverable | Form |
|---|---|
| **NIST 800-171 r3 evidence pack** | All 110 controls mapped; for each: control statement, our implementation, evidence pointer (logs/configs/screenshots), customer responsibility note. |
| **CMMC L2 readiness review** | Self-assessment against the 53 assessed controls. External pre-assessment with a C3PAO recommended (~5-day engagement). |
| **NIS2 + IEC 62443-3-3 SL-1 attestation** | Self-declared SL-1 with documented evidence. SL-2 targeted in Stage 3. |
| **On-prem HA reference** | NATS 3-node JetStream cluster (RAFT, R=3 streams), TimescaleDB primary + sync replica, ArangoDB cluster mode, Traefik HA pair. All customer-deployed. Documented RPO 1 min / RTO 5 min. |
| **DR runbook + quarterly drill** | Restore from immutable backup (S3 Object Lock or equivalent on customer's storage). Quarterly drill cadence locked. |
| **MFA + RBAC hardening** | TOTP/WebAuthn for admin paths. RBAC matrix documented and tested. |
| **Encryption-at-rest** | ArangoDB rocksdb encryption, TimescaleDB transparent encryption, JetStream stream-level encryption, secrets-at-rest via sealed-secrets or customer KMS. |
| **Vulnerability management** | Dependabot + Renovate + weekly vuln scan of release images. Public CVD policy (Coordinated Vulnerability Disclosure). |
| **Pen-test 2: comprehensive** | 10-day engagement. Full scope including HA topology. Findings tracked publicly. |
| **Incident response plan** | `/km/security/incident-response.md`. Roles, escalation, customer notification SLA (24h for critical), forensic preservation steps. |
| **Provisioning hardening** | Phase out USB cloud-init for staging. Move to bootstrap-cert + enrollment-server flow with two-person approval. |

**Exit criterion:** First production customer in defense supply chain. Customer's auditor accepts Progress deployment evidence without remediation findings on Progress's controls.

### Stage 3 — Product-level assurance (~12 months after Stage 2)

**Purpose:** Transition from "we help you certify your deployment" to "Progress Platform itself carries product-level assurance evidence." Funded by ≥3 paying defense customers.

| Deliverable | Form |
|---|---|
| **IEC 62443-4-1 secure development lifecycle** | Formal SDL: threat modeling per release, security testing gate, vulnerability handling, security update process. Audited by accredited lab. |
| **IEC 62443-4-2 component certification (SL-2 target)** | Progress Platform as a "host device" component. Lab engagement + remediation cycle. |
| **FIPS 140-3 validated crypto** | Migrate JWT/TLS to FIPS-validated libraries where customer requires (BoringSSL FIPS / Wolfcrypt / OS-provided FIPS modules). |
| **HSM-backed signing keys — remaining keys** | Cosign + deployment-manifest keys already in HSM since Stage 1 (see above). This stage migrates remaining keys — NATS Operator/Account signing keys, internal CA roots, customer-side cert-issuance keys — from sealed files to YubiHSM2 / AWS CloudHSM / Thales appliances. Managed Cloud uses AWS CloudHSM end-to-end. |
| **Reproducible builds** | SLSA Level 3 target. Build provenance attached to every release artifact. |
| **Annual pen-test cadence** | Locked. Findings published. Retest within 30 days of remediation. |
| **ISO 27001 ISMS** | Either certified or audited-equivalent. Underpins NIS2 + AQAP 2110 alignment. |
| **CMMC L2 third-party assessment** | C3PAO-issued certificate if a customer requires Progress to carry it directly. |

**Exit criterion:** IEC 62443-4-2 SL-2 certificate. Progress Platform listed as a certified component in at least one prime's approved-vendor list.

### Stage 4 — Sovereign / high-assurance options (~18+ months after Stage 3, revenue-gated)

**Purpose:** Optional posture for customers with sovereign / classified / cross-domain requirements. Not committed; documented as available scope.

- Air-gapped deployment profile (no outbound 443, internal-only Gitea mirror, offline update bundle workflow)
- Cross-domain guard / data diode integration patterns (NATS leaf → guard → secure side)
- TPM-attested provisioning
- IEC 62443-4-2 SL-3 uplift if commercially justified
- NATO STANAG 4427 configuration-management evidence pack
- Common Criteria EAL2/EAL3 evaluation
- Multi-region HA across sovereign datacenters

---

## The 10 deliverables from the prior review — mapped to stages

The prior CTO roadmap (May 2026) listed 10 deliverables in its "what I want to see before approving" section. Mapping each to the new stage model:

| # | Prior deliverable | Stage in new model | Notes |
|---|---|---|---|
| 1 | HA topology with failure domains + RPO/RTO | Stage 2 (on-prem HA reference) | On-prem first; Managed Cloud follows the same primitives |
| 2 | Threat model (STRIDE / LINDDUN) | Stage 0 v1, Stage 2 refresh, Stage 3 continuous | Required for the prospect meeting |
| 3 | Compliance matrix (NIS2 / 62443 / CRA) | Stage 0 v1, expanded each stage | Living document |
| 4 | External pen-test report | Stage 1 (focused), Stage 2 (comprehensive), Stage 3+ (annual) | Three engagements progressively wider |
| 5 | DR runbook + drill | Stage 2 | Quarterly cadence from Stage 2 onward |
| 6 | A/B rollback demo with bricked-image scenario | Stage 1 | Podman + systemd + Cosign, not docker.sock |
| 7 | Supply chain attestation (SBOM, signing, SLSA) | Stage 1 (signed builds + SBOM), Stage 3 (SLSA L3, HSM) | Sealed-file keys interim, HSM end-state |
| 8 | Decommissioning runbook | Stage 0 | Solved by markdown doc, low effort, high credibility |
| 9 | Bandwidth + cellular cost model | Stage 1 | Less critical on-prem (LAN) than for Managed Cloud |
| 10 | Bridge protocol matrix with security mode per protocol | Stage 0 (doc) + Stage 1 (enforcement) | OPC-UA SignAndEncrypt mandatory at config-load time |

---

## Critical files referenced

These are the files that the implementation phases will touch. Listed here so the reviewer can verify scope alignment:

- `deploy/config/nats-server.conf` — add TLS + decentralized auth (Stage 0/1)
- `deploy/compose/base.yaml` + new `deploy/compose/secure.yaml` — secure deploy profile (Stage 0)
- `backend/api/utils/nats_client.py` — credentials + cert handling on connect (Stage 1)
- `backend/api/utils/auth.py` — Ed25519 migration, JWKS endpoint (Stage 1)
- `backend/sparkplug_bridge/automations/pump_anomaly.py`, `backend/sparkplug_bridge/config.py` — token rotation, cert auth (Stage 1)
- `backend/sparkplug_bridge/kv_store.py` — KV bucket split + ACLs (Stage 1)
- `.planning/workstreams/sparkplug-demo/decisions/` — new ADRs: NATS auth chain, edge OTA model, mTLS PKI, KV governance (Stages 0–1)
- `km/security/` (new tree) — threat model, key custody, risk register, gaps, incident response (Stage 0+)
- `km/compliance/` (new tree) — matrix, evidence packs, auditor-facing docs (Stage 0+)
- `km/operations/secure-deploy.md` (new) — Stage 0 deliverable
- `.planning/codebase/CONCERNS.md` — bare-except + print() cleanup tracking (Stage 1)

---

## Existing patterns to reuse (do not reinvent)

Codebase survey confirms these already work and should be the foundation, not replaced:

- **Token lifecycle pattern** from ADR 0010 (`.planning/workstreams/sparkplug-demo/decisions/0010-*.md`) — file-mounted JWT with 0600 mode, dedicated service-account user (`USR-SPARKPLUG-BRIDGE`). Extend, don't rewrite.
- **JWT revocation via DB-backed Token collection** in `backend/api/utils/auth.py` — `_verify_token_base` already checks `revoked` flag and signature segment. Keep; add asymmetric-key migration as new code path.
- **Event-sourced audit trail** through `Event.save()` → `pre_processing()` → `apply()` → `store_event()` — already satisfies the AU-family controls in NIST 800-171 and the configuration-management evidence requirements of AQAP 2110. Document the mapping; don't add a separate audit log.
- **Traefik + Let's Encrypt + custom-cert file provider** per `km/architecture/https.md` — already handles external TLS termination. Extend for client-cert auth on admin paths; don't replace.
- **NATS KV bucket pattern** from `backend/sparkplug_bridge/kv_store.py` (`schema_version: 1`, idempotent hydration, JSON encoding) — reuse for `EDGE_DESIRED` / `EDGE_REPORTED` buckets.
- **pydantic-settings + Docker secrets pattern** in `backend/api/utils/config.py` — extend to load cert paths and signing keys; don't introduce a parallel config system.
- **ADR governance** in `.planning/workstreams/sparkplug-demo/decisions/` — proven `NNNN-kebab-title.md` with discussion → decided → implemented status pipeline. New security ADRs follow the same format.

---

## Open questions for the prospect meeting

These should be asked, not assumed. Listed in priority order — answers reshape the timeline.

1. **CUI status of the pilot:** Will the pilot touch CUI / ITAR-controlled / CGP-controlled technical data from day one, or is it Phase-1-non-CUI? Answer determines whether Stage 0 must include FIPS 140-3 crypto and CMMC L2 controls, or whether they belong in Stage 2.
2. **Customer's preferred PKI model:** Do they want to issue our certs from their CA, or accept our internal CA? Affects Stage 1 cert-management design.
3. **Deployment infrastructure:** Their datacenter, their cloud, or a mix? Air-gapped? Outbound-only firewall? Affects edge OTA design.
4. **Existing IDS/SIEM:** What do we forward to, in what format (syslog, CEF, OCSF, ECS)? Affects Stage 1 observability scope.
5. **Audit cadence they're already on:** ITAR registration date, CMMC assessment date, NIS2 deadline. Drives our Stage 2 evidence-pack timing.
6. **AS9100D auditor reuse:** Is the same auditor doing cybersecurity? If so, AS9100D 7.5 evidence reuse is straightforward.

---

## Review checklist before sending to the prospect

This document is a strategy artifact, not a code change. "Verification" means review by the right people before the prospect meeting:

1. **Solo review pass** — read top to bottom; confirm the on-prem framing is consistent; check no stage commits to deliverables that depend on Stage N+1 prerequisites.
2. **Sanity-check claims against repo state** — every "today we have X" claim in the *Honest current state* table is traceable to a file path. Verify each with `grep` or by reading the file before sending the doc out.
3. **External red-team read** — if a security-cleared contact is available, ask for a 1-hour read with one question: "would you sign this off if you were the prospect's CISO?" Adjust the gap list before the meeting if not.
4. **Dry-run the prospect conversation** — pick the three most-likely-to-be-asked questions (probable: HA story, supply-chain integrity, key custody) and rehearse the 2-minute answer against this doc.
5. **Lock the version sent to the prospect** — tag this doc as v1.0 once reviewed; everything after is a tracked revision.

---

## Bottom line for the prospect

What we will say in the room, distilled:

> Progress Platform is an open-source MOM serving AS9100D customers today. We do not claim defense-grade security posture today, and we will not pretend to. What we have is a clean event-sourced architecture, an existing JWT auth and revocation foundation, and a documented dual-track path — EU NIS2 + IEC 62443 baseline first, US NIST 800-171 / CMMC L2 evidence next — that reaches a pilot-ready state in roughly three months from kickoff and a production-ready, audit-evidence-complete state within twelve. Product-level IEC 62443-4-2 certification follows once a real customer commits. We invite you to verify every claim against our public repository.

That's a credible posture for a first conversation. It's also the truth.
