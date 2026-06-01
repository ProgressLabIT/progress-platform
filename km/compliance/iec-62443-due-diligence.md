# Progress Platform — IEC 62443 Due Diligence & Certification Track

**Author:** CTO, Progress Platform
**Status:** v0.1 draft
**Last updated:** 2026-06-01
**Audience:** internal compliance reference + basis for prospect-facing 62443 materials
**Companion documents:**
- `km/strategy/defense-aerospace-roadmap.md` — the five-stage security/compliance roadmap this track maps onto
- `km/security/iiot-security.md` — target security model (control plane, PKI, audit/compliance evidence)
- `km/security/tokens.md` — current API token lifecycle (HS256 today; Ed25519 on roadmap)
- `km/security/https.md` — Traefik / TLS termination

---

## 1. Purpose & scope

This document is the **62443-specific cut** of the broader compliance posture in `defense-aerospace-roadmap.md`. That roadmap bundles 62443 with NIST 800-171, CMMC L2, and NIS2; this document isolates what **IEC 62443 alone** demands of Progress *as a product*, grades current readiness against it, and defines a certification track that slots into the existing five stages.

It is the first deliverable of the `km/compliance/` tree (a Stage 0 line item in the defense roadmap, alongside the forthcoming `km/compliance/matrix.md`).

Scope is **high-level due diligence**, not an audit-ready control mapping. The control-by-control evidence mapping is `matrix.md`'s job.

---

## 2. Role & scope determination

62443 is a family of standards, not a single certificate. What applies depends on the **role** being certified. Progress wears two hats:

| Role | Relevant parts | Who certifies |
|---|---|---|
| **Product supplier** (Progress as software) | **62443-4-1** (secure development *lifecycle*) + **62443-4-2** (component *technical* requirements) | **Progress** — this is our product certification |
| Enabler of the **asset owner / system integrator** (customer's plant) | 62443-2-1, **62443-3-3** (system requirements / Security Levels) | The **customer** certifies their IACS; Progress supplies evidence and a hardened reference deploy |

The product-supplier hat is the one Progress can certify directly. The asset-owner/integrator hat is a *support* obligation — we provide the audit evidence (`iiot-security.md` §7) and a secure-deploy profile, but the customer holds those certs.

### 2.1 Component type under 62443-4-2 — **Software Application**

62443-4-2 defines four mutually exclusive component classes, each with its own requirement set:

| Class | Requirement set | Fits Progress? |
|---|---|---|
| **Software Application (SAR)** | Software running on a host OS | ✅ **Primary scope** — the FastAPI/DB/webapp stack |
| Host Device (HDR) | A general-purpose device hosting software | Only if the edge IPC is sold as a sealed appliance |
| Embedded Device (EDR) | Special-purpose, firmware-based | The bridge IPC, if shipped as an appliance |
| Network Device (NDR) | Routers, switches, firewalls | ❌ N/A |

**Decision:** certify the core platform as a **Software Application (SAR)**. The edge IPC, *if and when* it ships as a sealed appliance, becomes a separate later EDR/HDR scope — do not conflate the two.

> **Correction to existing docs:** `km/strategy/defense-aerospace-roadmap.md:138` (Stage 3 table) currently states *"Progress Platform as a 'host device' component."* That is the wrong component class for a software product and changes which CRs we are audited against. Should read **Software Application**.

### 2.2 Target Security Level — **SL 2**

62443 grades both system (3-3) and component (4-2) requirements on Security Levels SL 1–4 by attacker capability:

- **SL 1** — protection against casual/coincidental violation.
- **SL 2** — intentional violation, *simple* means, low resources, low motivation. **← commercial sweet spot, our target.**
- SL 3 — sophisticated means, IACS-specific skills, moderate resources. Sovereign/Stage 4 only.
- SL 4 — sophisticated means, extended resources. Not in scope.

**Decision:** baseline **SL 1** evidence first, **SL 2 as the certification target**, **SL 3 deferred to the sovereign Stage 4** posture. This matches the existing roadmap. The SL-1 → SL-2 jump is where the real engineering lives (MFA, role-based authorization, stronger crypto) — see §4.

---

## 3. Current-state readiness vs the 7 Foundational Requirements

Graded against where the **product is today**, not the roadmap target.

| FR | Requirement | Today | Grade |
|---|---|---|---|
| **FR1 — Identification & Authentication Control** | HS256 JWT (`backend/api/utils/auth.py`), DB-backed revocation via `Token` collection, single active session/user; NATS plain TCP, no auth; no MFA | Authentication exists, but symmetric key + no MFA + unauthenticated message bus | 🟡 partial |
| **FR2 — Use Control** | `Depends(auth.verify_token)` gates endpoints — but **no role/permission model exists** in `backend/`. Authorization is binary: a valid token grants full access | **The long pole.** SL-2 mandates role-based authorization with least privilege | 🔴 gap |
| **FR3 — System Integrity** | Event-sourced immutability (`Event.save()` chain), Pydantic v2 at all boundaries, Cosign + signed-manifest supply chain designed (`iiot-security.md` §3) | Architecturally strong; the supply-chain story is a differentiator | 🟢 strong |
| **FR4 — Data Confidentiality** | mTLS + at-rest encryption *designed* but not implemented; `ARANGO_NO_AUTH=1` in dev compose; NATS plain TCP | Roadmapped (Stage 1), not built | 🔴 gap |
| **FR5 — Restricted Data Flow** | Outbound-only edge [P4], network namespaces + `nft` firewall, tightest-possible NATS ACLs (`iiot-security.md` §3.3, §4) | Excellent zone/conduit posture; needs the formal zone/conduit diagram as evidence | 🟢 strong |
| **FR6 — Timely Response to Events** | Event store = near-free immutable audit trail; `audit.*` NATS subjects + pgAudit planned; HTTP error logging (30-day TTL); SIEM forwarding roadmapped | Event-sourcing is a genuine 62443 advantage here | 🟢 strong |
| **FR7 — Resource Availability** | JetStream backpressure, backup/DR, HA all roadmapped (Stage 2); no rate-limiting / DoS protection today | Designed, not built | 🟡 partial |

### 3.1 Headline findings

- **The architecture buys FR3 / FR5 / FR6 nearly for free.** Event-sourcing (immutable, ordered, exportable event store) and the outbound-only edge with `nft`-enforced OT/IT separation are doing heavy 62443 lifting that most vendors retrofit painfully. This is the credible core of the 62443 story.
- **FR2 (Use Control) is the one real, under-served gap.** There is no authorization model today — only authentication. It appears in the existing roadmap solely as a Stage 2 one-liner ("MFA + RBAC hardening"). For 62443-4-2 SL-2, role-based access control with least privilege is foundational, it touches the endpoint/event layer broadly, and retrofitting it late is expensive. **It warrants its own ADR and an earlier phase.**
- **FR4 is a known, scoped gap** — mTLS and encryption-at-rest are already designed and slotted into Stage 1; no re-planning needed, just execution.

---

## 4. 62443-4-1 readiness (secure development lifecycle)

4-1 certifies the **process**, not the product, across eight practices. Much already exists informally — the task is to *formalize and evidence*, not invent:

| Practice | 62443-4-1 area | Current state |
|---|---|---|
| **SM** — Security Management | Defined SDL, roles, expertise | ADR governance + this compliance tree; needs a documented SDL policy |
| **SR** — Specification of Security Requirements | Per-feature security requirements | Per-phase threat notes in some `PLAN.md`; needs per-release security requirements |
| **SD** — Secure by Design | Threat modeling, defense in depth | Event-sourcing + outbound-only edge are secure-by-design; needs a platform threat model (Stage 0 deliverable) |
| **SI** — Secure Implementation | Secure coding, review | Pydantic boundaries; **62 bare `except:` + 44 `print()`** flagged in `CONCERNS.md` are audit-trail risks to clear |
| **SVV** — Security Verification & Validation | Security test gate | Integration suite exists; needs an explicit security V&V gate in CI |
| **DM** — Defect Management | Vulnerability handling | Dependabot/Renovate planned; event store gives defect traceability; needs a documented process |
| **SUM** — Security Update Management | Patch/update delivery | **Strong** — the Cosign-signed, content-addressed, A/B OTA channel (`iiot-security.md` §3) *is* the update process |
| **SG** — Security Guidelines | Hardening guide for users | Needs a customer-facing hardening/secure-deploy guide (`km/operations/secure-deploy.md`, Stage 0) |

**Net:** SM/SD/SUM are in good shape; SR/SVV/DM/SG need formalization. 4-1 is mostly documentation and is reusable across every future product and every regime (it doubles as ISO 27001 / NIST SSDF / AQAP 2110 process evidence).

---

## 5. Certification path & body

- **4-1 before 4-2.** ISASecure's component certification (CSA) requires a maintained SDL as a prerequisite — the product cannot be certified without the process certification first. 4-1 is also higher-leverage (documentation, reusable across products/regimes).
- **Certification scheme — default ISASecure.** ISASecure (ISA/IEC, governed by ISCI; accredited labs include exida and TÜV Rheinland) runs the most widely recognized **SDLA** (for 4-1) and **CSA** (for 4-2) certifications — what a defense prime's approved-vendor list will recognize. Alternatives: TÜV's own 62443 scheme, or UL. **Decision: default to ISASecure** unless the EU prospect names a preferred body.

---

## 6. Roadmap — the 62443 track mapped onto the five stages

This track does not replace the five-stage roadmap; it is the 62443 thread *through* it.

| Phase | 62443 work | Maps to roadmap stage |
|---|---|---|
| **A — Scope & self-assess** | Lock role (product supplier), component class (Software Application), target SL-2. Self-assessment vs 4-1's 8 practices + 4-2's 7 FRs (this document). Pick cert body. Produce zone/conduit diagram (FR5 evidence). | **Stage 0** (`km/compliance/`) |
| **B — Close 4-2 technical gaps** | mTLS everywhere (FR4) · **RBAC + least-privilege model (FR2) — own ADR** · asymmetric tokens + MFA on admin/untrusted paths (FR1) · NATS decentralized auth (FR1) · audit tamper-evidence + time-sync (FR6) · backpressure / backup / rate-limit (FR7) | **Stage 1–2** |
| **C — Stand up the 4-1 SDL** (parallel) | Formalize SR/SVV/DM/SG: per-release security requirements, security V&V CI gate, documented vuln handling + public CVD, user hardening guide. Clear the bare-`except`/`print` audit-trail debt. | **Stage 1–3** |
| **D — Lab pre-assessment** | Engage ISASecure lab (exida/TÜV) for a gap assessment against SL-2; remediate P1/P2. | **Stage 2–3** |
| **E — Certify** | 4-1 SDLA certificate → 4-2 CSA SL-2 certificate. | **Stage 3** |

---

## 7. Decisions register

Captured in-document because formal `.planning/` ADRs cannot live on `DEV` (planning artifacts stay on feature branches). Promote these to standalone ADRs when the 62443 work gets its own worktree/workstream.

| # | Decision | Status | Rationale |
|---|---|---|---|
| D1 | Certify the core platform as a **62443-4-2 Software Application (SAR)**, not a host device | decided | Correct component class for a software product; changes which CRs apply. Corrects `defense-aerospace-roadmap.md:138` |
| D2 | **Target SL 2** (SL-1 baseline, SL-3 deferred to Stage 4) | decided | Commercial sweet spot; matches existing roadmap |
| D3 | **4-1 SDLA before 4-2 CSA**; **ISASecure** as default certification scheme | decided | CSA requires a maintained SDL; ISASecure is the most recognized scheme. Revisit if prospect dictates a body |
| D4 | **Pull RBAC / FR2 out of the Stage 2 one-liner into an earlier, dedicated phase with its own ADR** | discussion | Only foundational SL-2 gap not already designed; broad blast radius; expensive to retrofit late |
| D5 | Edge IPC appliance certified separately as **EDR/HDR**, later, if shipped as a sealed appliance | discussion | Keep software and appliance scopes distinct |

---

## 8. Open questions

1. **RBAC model shape** (D4): role taxonomy (operator / supervisor / admin / service), enforcement layer (endpoint dependency vs event-layer vs both), and how it interacts with the existing single-session JWT model. Needs its own ADR before implementation.
2. **Appliance scope** (D5): will Progress ever ship the edge IPC as a sealed appliance, or remain software-only? Determines whether an EDR/HDR scope is ever in play.
3. **Prospect-dictated certification body**: does the EU defense prospect require a specific scheme (e.g., a TÜV cert) that would override the ISASecure default?

---

## 9. Cost & funding gate

A combined 4-1 SDLA + 4-2 CSA SL-2 lab engagement is realistically **€50–150k** plus months of internal effort. The existing roadmap correctly gates the **certification** (Phases D–E) behind **≥3 paying defense customers** — nothing here changes that. What this due diligence *does* change: **begin the RBAC/FR2 work (Phase B) earlier than Stage 2**, because it is a prerequisite for any SL-2 audit and is cheap to design now, expensive to retrofit later.

---

## 10. References

**Internal:**
- `km/strategy/defense-aerospace-roadmap.md` (component-class correction pending at :138 — see §2.1 / D1)
- `km/security/iiot-security.md`
- `km/security/tokens.md`, `km/security/https.md`
- `.planning/codebase/CONCERNS.md` (bare-except / print audit-trail debt)

**External standards:**
- IEC 62443-4-1 — Secure product development lifecycle requirements
- IEC 62443-4-2 — Technical security requirements for IACS components (SAR/HDR/EDR/NDR)
- IEC 62443-3-3 — System security requirements and security levels
- ISASecure — SDLA (4-1) and CSA (4-2) certification schemes (ISCI)

---

## 11. Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | 2026-06-01 | CTO | Initial 62443 due-diligence cut extracted from the defense roadmap; role/scope determination, 7-FR readiness grade, 4-1 practice readiness, certification track, decisions register. First `km/compliance/` deliverable. |
