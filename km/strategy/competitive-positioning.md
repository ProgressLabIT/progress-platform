# Progress Platform — Competitive Positioning & Open-Source Strategy

**Author:** CTO, Progress Lab
**Status:** v0.1 draft
**Last updated:** 2026-05-27
**Audience:** internal strategy; basis for prospect- and community-facing positioning
**Companion documents:**
- `km/architecture/iiot-architecture.md` — IIoT architecture (topology, data plane, federation)
- `km/security/iiot-security.md` — IIoT security model
- `km/strategy/defense-aerospace-roadmap.md` — security & compliance posture roadmap
- `km/strategy/arangodb-migration.md` — substrate licensing/migration analysis

---

## 1. Purpose

Record how Progress Platform positions against the IIoT / manufacturing-data incumbents, and why **Progress Lab's open-source, whole-ecosystem bet is a genuinely different play** — not a feature-parity race against well-funded proprietary platforms. This document exists so that scope decisions, prospect conversations, and community messaging stay anchored to a deliberate strategy rather than drifting into "catch up to incumbent X."

---

## 2. The landscape

Two players are close to what Progress is building on the IIoT/data-substrate side. Neither is a like-for-like competitor; each overlaps a different slice.

| | Layer | Substrate | Ships apps? | Manufacturing semantics | Licensing / market | Compliance posture |
|---|---|---|---|---|---|---|
| **i-flow** (DE) | UNS / Industrial DataOps — *below* the MOM | MQTT + NATS (supercluster federation) | No | None — data-agnostic | Proprietary; enterprise (Bosch Rexroth, Hirschvogel; 750M ops/day) | Minimal/unstated |
| **Rhize** | ISA-95 semantic data hub / headless MES backend — *overlaps the MOM core* | NATS + knowledge graph (ISA-95 ontology) | **No (headless — BYO frontend)** | ISA-95 2018 as formal graph schema; GraphQL; BPMN orchestration | Proprietary; **enterprise (our understanding: ~€200k/yr per site + services)** | Not emphasized |
| **Progress** (Progress Lab) | Full event-sourced MOM — apps + substrate + compliance | NATS (JetStream) + ArangoDB graph | **Yes — production, inventory, quality, warehouse** | Event-sourced domain models + genealogy graph; ISA-95 as logical label | **Open source**; on-prem-first, single-tenant | AS9100D today; defense/aerospace roadmap |

### Reading the table

- **i-flow** is the data-plane plumbing that would sit *beneath* Progress: autonomous m:n integration, contextualization, UNS. It has no manufacturing semantics and no applications.
- **Rhize** is architecturally the closest to Progress — NATS, graph DB, event-driven, targets serialized discrete manufacturing — but it is **headless** (a backend you assemble an MES on top of) and bets everything on a **formal ISA-95 ontology** exposed over GraphQL. It is sold as an enterprise platform at enterprise prices.
- **Substrate convergence:** both i-flow and Rhize independently chose **NATS** as the manufacturing substrate. With Progress having already moved Kafka→NATS, this is strong external validation of the single most foundational architectural bet in the stack.

---

## 3. The Progress Lab thesis

Progress Lab is not trying to out-feature i-flow or Rhize. The bet is a **different axis of value**:

> **A complete, open-source suite covering the whole operational-data ecosystem — substrate, applications, historian, reports, and IIoT connectivity — shipped as on-prem, auditable, single-tenant tools.**

The four pillars that make this genuinely different from both incumbents:

1. **Open source.** Both i-flow and Rhize are proprietary, enterprise-priced (Rhize reportedly ~€200k/yr per site + services). Progress is open source. For engineering-led shops, cost-sensitive manufacturers, and especially defense/aerospace customers who need an *auditable substrate with no vendor black boxes*, this is a structural advantage, not a discount.
2. **Whole-ecosystem suite, not a layer.** i-flow gives you plumbing; Rhize gives you a headless backend. Both require you to assemble the rest. Progress ships the whole stack — NATS substrate + event-sourced MOM (production tracking, inventory, traceability, quality) + Timescale historian + Streamlit reports + IIoT protocol bridges (Sparkplug B, OPC-UA, Modbus TCP, ...) — as one coherent product. You don't integrate five tools; you deploy one.
3. **On-prem-first, single-tenant, auditable.** Same primitives on-prem and in Managed Cloud. No data-egress economics, no sovereignty problem, no opaque substrate.
4. **Compliance as a primitive.** Event sourcing makes the AS9100D audit/genealogy story free; the defense/aerospace roadmap (NIST 800-171, CMMC, IEC 62443) builds on that. Neither incumbent leads with this.

**The honest trade:** we will **not** match the feature depth, connector breadth, or operational maturity (HA, autonomous mapping, BPMN tooling) of well-funded proprietary platforms in the near term. The bet is that **open + complete-ecosystem + on-prem + compliance** beats **proprietary feature-depth** for our target customer — the regulated, multi-vintage, open-source-receptive discrete manufacturer. We win on coherence, cost, auditability, and ownership, not on having the most connectors.

---

## 4. What we deliberately are NOT doing

Stated so scope creep can be checked against intent:

- **Not headless.** We ship the applications. (This is the clearest wedge against Rhize.)
- **Not productizing autonomous m:n tag mapping** as the headline feature. (That is i-flow's game; we normalize in-bridge.)
- **Not adopting per-site enterprise licensing.** Open source is the distribution model; monetization is support / Managed Cloud / services (see §5).
- **Not (currently) adopting ISA-95 as the formal data schema.** We use ISA-95 as a logical label over event-sourced domain models, not as the ontology (cf. `iiot-architecture.md` §3.2). See open question §5.

---

## 5. Open strategic questions

These are real forks, not rhetorical. Each should eventually reach an ADR or roadmap decision.

1. **ISA-95 ontology layer — formalize or keep as logical label?** Rhize bets that a formal ISA-95 ontology + GraphQL = data portability and integrator appeal. Progress deliberately treats ISA-95 as a logical label. A sophisticated prospect *will* ask "why isn't your model ISA-95-native?" — we need an answer that is a *choice*, not an omission. Decision pending; candidate: a thin ISA-95 semantic/export layer over the event store rather than a schema rewrite.
2. **Build vs. partner on the UNS substrate.** Do we build the full UNS data-plane ourselves (compete with i-flow) or treat a UNS layer as substrate and focus on the MOM + compliance on top? Both speak NATS, so integration is near-trivial. For solo capacity, partnering/consuming is the leverage play; owning it is justified only if the substrate itself is the product.
3. **Open-source monetization model.** The OSS bet must fund a defense-grade compliance roadmap. Support contracts, Managed Cloud, and services are the obvious levers; a dual-license or open-core boundary is the harder question. This is the same gap as `defense-aerospace-roadmap.md` §"commercial-support function shape." Unresolved and load-bearing — the strategy only works if the revenue model does.

---

## 6. Bottom line

Progress Lab is not the cheap clone of Rhize or the apps-on-top-of-i-flow. It is a **different category**: the open-source, whole-ecosystem operational-data suite for regulated discrete manufacturers — shipped complete, run on-prem, auditable by construction. The incumbents validate the architecture (NATS, graph, event-driven, ISA-95 context) and the market (serialized discrete manufacturing, on-prem demand). Our differentiation is the *model* — open, complete, owned by the customer — not the feature count.

---

## 7. Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | 2026-05-27 | CTO | Initial draft. Captures the i-flow / Rhize competitive read, the NATS-substrate convergence signal, and the Progress Lab open-source whole-ecosystem thesis. Competitor pricing figures are internal estimates, not verified public data. |
