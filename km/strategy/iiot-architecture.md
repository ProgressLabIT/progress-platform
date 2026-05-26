# Progress Platform — IIoT Strategy and Architecture

**Author:** CTO, Progress Platform
**Status:** v0.1 draft
**Last updated:** 2026-05-21
**Audience:** internal strategy + technical reference; basis for prospect-facing materials
**Companion documents:**
- `km/strategy/defense-aerospace-roadmap.md` — security & compliance posture roadmap
- `km/strategy/arangodb-migration.md` — substrate migration analysis
- `.planning/workstreams/sparkplug-demo/decisions/0011-database-substrate.md`
- `.planning/workstreams/sparkplug-demo/decisions/0012-graph-query-substrate.md`
- ADRs 0001–0010 in `.planning/workstreams/sparkplug-demo/decisions/`

---

## 1. Purpose of this document

Establish a single reference for Progress Platform's IIoT approach — strategic positioning, design principles, and the corrected architecture that supersedes the original "IIoT Edge-to-Cloud Architecture Specification v1.0" (May 2026, single-cloud-node, docker.sock-based update model). The original spec captured the right *intent* (decoupled OT/IT, NATS as unified data plane, outbound-443 connectivity, edge buffering) but the *security, supply-chain, and HA* dimensions need substantial rework — done here.

This document is the place to point when an engineer, partner, or prospect asks "how does Progress Platform actually approach IIoT?" It deliberately stays at strategy + architecture; per-component implementation lives in ADRs and `km/architecture/`.

---

## 2. Strategic positioning

### 2.1 Customer profile

Progress Platform targets discrete-manufacturing operations with three converging characteristics:

- **Quality- and traceability-driven** — typically AS9100D, IATF 16949, ISO 13485, or equivalent regulated-sector certification. The audit and genealogy story matters more to them than dashboard polish.
- **Multi-facility, mixed-vintage estate** — they operate across multiple plants with heterogeneous OT environments (different PLC vendors, different network maturity, different existing local systems). They want unification without rip-and-replace.
- **Open-source-receptive** — either by preference (engineering culture), economics (escape from per-tag licensing), or compliance posture (auditable substrate, no vendor black boxes for defense/aerospace flow-down).

Two adjacent profiles where Progress fits but is not the obvious first choice:
- **Single-facility SMEs with no IIoT today** — we work, but Ignition / ThingsBoard / Litmus Edge are aimed squarely at this segment and have larger ecosystems.
- **Process-industry continuous manufacturing** — historian-centric (PI, AVEVA) remains entrenched; Progress is discrete-manufacturing-first.

### 2.2 Positioning relative to incumbents

| Incumbent | What they do well | Where Progress differs |
|---|---|---|
| **Ignition (Inductive Automation)** | Mature SCADA + MES, strong integrator network, unlimited-tag licensing | Closed substrate, per-server licensing, weak audit-trail/traceability story for AS9100D, Java/JVM operational footprint |
| **AVEVA System Platform / Wonderware / OSIsoft PI** | Industry-defining historian, deep process-industry penetration | Heavy commercial licensing, per-tag/per-server pricing, closed substrate, hostile to OSS-stack integration |
| **Siemens Industrial Edge / MindSphere** | Tight coupling with Siemens PLCs, enterprise scale | Vendor lock-in to Siemens ecosystem; multi-vendor estates suffer |
| **AWS IoT TwinMaker / Azure IoT** | Cloud-native scale, managed services | Cloud-first (not on-prem-first), heavy data-egress economics, sovereignty challenges for defense/aerospace, opaque substrate for audit |
| **ThingsBoard Community / Open MES projects** | Open source, low entry cost | Generally weaker on event-sourced traceability, audit-trail-as-product, and discrete-manufacturing semantics |

**The Progress positioning sentence:** *Open-source, event-sourced manufacturing operations + IIoT substrate, designed on-prem-first for multi-facility discrete manufacturers in regulated industries (AS9100D, defense/aerospace, life-sciences). Audit trail and traceability are architectural primitives, not features. mTLS and decentralised auth are defaults, not options.*

### 2.3 In scope / out of scope

**In scope:**
- Plant-floor equipment connectivity (Sparkplug B today; OPC-UA next; Modbus TCP / EtherNet/IP / S7 as bridge-protocol roadmap items)
- Edge data buffering (offline-first), telemetry normalisation, alarm/event handling
- Production tracking (work orders, jobs, phases, operations) — Progress core
- Inventory + traceability (serials, lots, BOM, genealogy) — Progress core
- Quality (issues, NCRs, FAIR linkage) — Progress core
- Historian for time-series telemetry (Timescale on Postgres)
- KPI / OEE / dashboards (Streamlit-based reports; Quasar SPA for transactional UI)
- ISA-95 logical hierarchy as the contextual taxonomy
- Audit trail by construction (event sourcing)
- On-prem and Managed Cloud deployment (same primitives)
- Defense/aerospace security posture, on roadmap (see companion doc)

**Out of scope (will not pursue):**
- Closed-loop control or safety functions (telemetry-only; no PLC writeback in critical paths; no SIL claim)
- Process-industry historian features competing with AVEVA PI (we don't try to be a PI replacement for refineries)
- Asset-performance-management ML platform (we provide the substrate; ML lives in customer's analytics estate or in opinionated reports)
- DCS / SCADA replacement — we are the layer above SCADA, not its substitute
- Vendor-locked PLC programming or asset config tooling (we read telemetry; we don't program the PLC)

### 2.4 Design principles

Six principles that drive every architectural decision:

1. **Event-sourced everything that matters.** Every state-changing action is an immutable, queryable event before it is a mutation. This makes traceability, audit, and AS9100D evidence chains *free*, not bolt-on. (Established in `backend/api/events/`, 50+ event types, `Event.save()` → `pre_processing()` → `apply()` → `store_event()` transaction chain.)
2. **On-prem first; Managed Cloud uses the same primitives.** No architecture or feature exists *only* in cloud. The customer's deployment model is a config choice, not a different product.
3. **Decoupled OT/IT respecting Purdue.** Edge container topology is designed so PLC-facing components live on the OT-facing network interface and IT-facing components live on the IT-facing one. No flat collapse.
4. **Outbound-only edge.** Edge IPCs never accept inbound from the IT-side network. All cloud (or central on-prem) ingress is outbound from the edge, port 443 (or customer's allowed egress), TLS.
5. **mTLS and decentralised JWT auth as defaults.** Not optional, not "advanced configuration." Every NATS, API, and service-to-service connection is mutually authenticated with cryptographic identities derived from a documented PKI.
6. **Signed, A/B, rolled-back-on-failure updates.** No update is fire-and-forget. Every component is delivered as a signed image (Cosign), deployed into one of two slots, health-gated, and automatically reverted on probe failure. No `docker.sock` exposure to any container.

These principles are referenced throughout the architecture section as **[P1]–[P6]**.

---

## 3. Architecture — the corrected reference model

This section supersedes the original "IIoT Edge-to-Cloud Architecture Specification v1.0." The original captured the right *shape*; what changes here is the security, supply-chain, HA, and federation detail.

### 3.1 Topology overview

The deployment fans out across three concentric scopes:

```
┌─────────────────────────────────────────────────────────────────┐
│  ENTERPRISE TIER  (per region — NA / EU / APAC as needed)       │
│  • Central NATS cluster (3-node, JetStream RAFT)                │
│  • Progress API (FastAPI, HA pair behind Traefik)               │
│  • PostgreSQL + Timescale + (AGE or CTE) — Patroni cluster      │
│  • Object storage for backups (immutable / Object Lock)         │
│  • Gitea (or other OCI-compliant registry) + Cosign keyserver   │
│  • Observability stack (Prometheus + Loki + Grafana)            │
└──────────────────────▲──────────────────────────────────────────┘
                       │  outbound-only WSS:443, mTLS-mutual
                       │  Federation policy: data-class-aware
┌──────────────────────┴──────────────────────────────────────────┐
│  FACILITY TIER  (per plant — 1 per facility)                    │
│  • NATS Leaf Node (JetStream buffer, offline-first)             │
│  • Edge Aggregator + Local Reports (optional facility-local)    │
│  • Edge Bridge(s) — protocol-specific (Sparkplug B, OPC-UA,…)   │
│  • Edge Update Agent (podman + systemd; NO docker.sock)         │
└──────────────────────▲──────────────────────────────────────────┘
                       │  OT VLAN — physically/logically separate
┌──────────────────────┴──────────────────────────────────────────┐
│  OT TIER  (per cell / line)                                     │
│  • PLCs, sensors, equipment (Siemens, Rockwell, Mitsubishi, …)  │
│  • Sparkplug B Edge of Network nodes (where supported)          │
│  • OPC-UA endpoints (SignAndEncrypt required, no fallback)      │
└─────────────────────────────────────────────────────────────────┘
```

Four architectural facts to internalise:

1. **OT tier and Facility tier are on different L2 networks.** The edge host has at least two NICs; the bridge container binds to the OT-facing one for ingress and the IT-facing one for egress. In single-host deployments (the default — see §3.4), network namespaces + host firewall rules enforce the separation. In dual-host variant, the separation is physical. **[P3]**
2. **Edge → Enterprise is always outbound.** No inbound port opened on the edge's IT-facing interface. NATS leaf-node connection initiates from the edge over WSS:443. **[P4]**
3. **Enterprise tier is per region, on the customer's private network by default.** Not "one global cloud," not internet-exposed unless the customer chooses Managed Cloud. On-prem deployments place Enterprise NATS on the customer's corporate WAN / MPLS / site-to-site VPN; sites in each region route to their regional Enterprise instance; cross-region replication is **data-classification-aware** (see §3.6). Managed Cloud uses the same primitives behind Traefik + mTLS on internet-routable endpoints — the outbound-from-edge property is preserved. **[P2]**
4. **The edge's control plane is one cryptographically gated channel.** Inbound to the edge from the Enterprise tier consists of exactly two things: (a) a single NATS KV key watch (`EDGE_DESIRED.{uuid}`) carrying a signed deployment manifest, and (b) HTTPS GETs to the registry for image layers (by digest). Nothing else. This collapses the customer-side firewall ACL to two lines and is the architectural primitive that makes the rest of the security model defensible. **[P5, P6]**

That fourth point matters for procurement: the customer's network team can write a one-line outbound ACL ("WSS:443 to `nats.region.customer.example.com`; HTTPS:443 to `registry.region.customer.example.com`; drop everything else") and defend it in audit. We do not ask them to open inbound ports, accept arbitrary protocols, or trust a vendor-specific tunnel.

### 3.2 Data plane — NATS

NATS is the unified messaging substrate for both telemetry and control. JetStream provides durability; KV provides distributed state.

**Subject taxonomy** (per ADR-0002, extended for IIoT):

```
telemetry.{enterprise}.{site}.{area}.{line}.{workcell}.{equipment}.{metric}
events.{domain}.{event_type}                  # event-sourced platform events
sparkplug.raw.{group}.{edge}[.{device}]       # raw Sparkplug B frames (per ADR-0008)
edge.desired.{equipment_uuid}                 # desired-state KV channel (CI → edge)
edge.reported.{equipment_uuid}                # reported-state KV channel (edge → ops)
audit.{component}.{action}                    # security-relevant audit events
```

**ISA-95 path as logical label, equipment UUID as stable key.** The ISA-95 hierarchy (`enterprise.site.area.line.workcell.equipment`) is the *human-readable* contextual taxonomy. The primary key for an asset is a stable UUID. ISA-95 path is an attribute on the asset that can change (re-org, line renumbering, equipment moved) without breaking historian continuity or KV state references. This was the single largest mistake in the original spec and is corrected here.

**KV buckets** (governance per ADR-0011/0012):

| Bucket | Writer | Reader | Purpose |
|---|---|---|---|
| `EDGE_DESIRED` | CI/CD only | Edge read-only | Target image refs, config revisions, rollout commands |
| `EDGE_REPORTED` | Edge only | Ops dashboards, CI/CD read-only | Active image, health, last-seen, telemetry buffer depth |
| `SPARKPLUG_SESSIONS` | Bridge | Bridge | Per-edge / per-device session state (bd_seq, alive, gaps) — existing per `backend/sparkplug_bridge/kv_store.py` |
| `SPARKPLUG_ALIASES` | Bridge | Bridge | Metric alias mappings (existing) |
| `SPARKPLUG_LAST_SEQ` | Bridge | Bridge | Last sequence per session (existing) |
| `SPARKPLUG_LAST_VALUES` | Bridge | Reports, UI | Last good value per metric (existing) |

Bucket ACLs are enforced per-NATS-account. Edge accounts cannot write `EDGE_DESIRED`; CI accounts cannot write `EDGE_REPORTED`. ACL drift is itself an alert.

**Backpressure policy** (replaces the original spec's hand-wave):

- Each JetStream stream has explicit `max_bytes`, `max_age`, and `discard_policy: old` configured at creation.
- Per-site disk budget is documented per deployment size class (small / medium / large) in `km/operations/edge-sizing.md` (to be written in Stage 1).
- Edge reports buffer depth into `EDGE_REPORTED.buffer_depth`; central monitoring alerts at 70% and pages at 90%.
- Backfill replay on reconnect is **rate-limited and downsampled** for telemetry older than a configurable threshold (default: 1 hour). Raw historical replay over cellular would otherwise saturate the link. Customers can opt into full-fidelity replay where bandwidth permits.

### 3.3 Control plane — signed deployment manifests, content-addressed images

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

**What it takes to compromise the edge through this control plane:**

Three independent compromises are required:

1. **Deployment-signing key** — offline, in HSM or sealed file with documented custody chain (see §3.7 and `defense-aerospace-roadmap.md`).
2. **Cosign signing key** — separate, also offline, separate custody.
3. **Registry write access** — to host the malicious image bytes.

Two-person integrity on either signing key raises this to four or five compromises with separation of duties. This is the same threshold that protects production OS update channels at major OS vendors.

**Key properties of the validation pipeline:**

- **Content-addressed.** Image references in the manifest are SHA-256 digests, never tags. Registry becomes untrusted byte distribution; even a fully compromised registry can only serve the exact bytes the manifest already pinned.
- **No `docker.sock` exposure.** The Update Agent runs under a constrained systemd unit and invokes `podman` directly. No container has access to the container runtime control socket. **[P6]**
- **Strict, fuzzed parser.** The manifest parser is minimal and treated as a security-critical component — fuzzed continuously, audited every release. Manifest parser CVEs are the highest-severity incident class on the edge.
- **Downgrade protection.** A compromised manifest-signer cannot push an old, vulnerable-but-validly-signed image because `minimum_version` is enforced. (Eventually: chained-revocation list with explicit deny entries.)
- **Replay protection.** `effective_from` rejects stale manifests; combined with KV revision numbers, an attacker who captured an old manifest cannot replay it later.
- **Rollback writes `EDGE_REPORTED`, not `EDGE_DESIRED`.** Rollback never modifies the desired state, so the operations dashboard surfaces failures without ping-pong loops between Agent and CI.
- **Phased rollout enforced at the orchestrator.** CI writes manifests in cohorts (5% → 25% → 100%) with bake periods, jitter on edge watchers, and pull-through registry caches at regional and facility levels to avoid thundering herd.

**NATS account permissions on the edge (the silent prerequisite).** The edge's NATS user has the tightest possible permission grant:

- *Subscribe* on `EDGE_DESIRED.{its-uuid}` only — no wildcards, no other subjects.
- *Publish* on `telemetry.{its-isa-95-path}.*`, `events.{...}`, `EDGE_REPORTED.{its-uuid}` only.
- *No* request/reply, *no* KV write outside its own `EDGE_REPORTED` entry.

An ACL slip here undoes the entire security model. This is verified on every deploy by an automated ACL-diff check and surfaced in the security ADR for the deployment.

This update model supersedes the original spec's `docker.sock`-based Agent pattern outright. ADR documenting the design is pending; `km/operations/edge-ota.md` is the Stage 1 deliverable.

### 3.4 Edge architecture

#### 3.4.1 Single-host reference deploy (the default)

A single edge IPC runs all edge functions in containers under podman + systemd. This is the right architecture for the demo, pilots, and the majority of production sites. Concretely:

```
┌───────────────────────────────────────────────────────────────┐
│  Edge IPC  (single host, dual NIC)                            │
│                                                                │
│  ┌─────────────────────┐    ┌─────────────────────────────┐   │
│  │ Bridge container    │    │ NATS Leaf container         │   │
│  │ (Sparkplug / OPC-UA │───►│ (JetStream buffer)          │   │
│  │  / Modbus reader)   │    │                             │   │
│  │ binds OT NIC only   │    │ binds IT NIC only           │   │
│  └─────────────────────┘    └──────────────┬──────────────┘   │
│             ▲                              │ WSS:443 outbound │
│             │                              │ mTLS-mutual      │
│             │                ┌─────────────▼──────────────┐   │
│  ┌──────────┴────────┐       │ Edge Update Agent          │   │
│  │ podman + systemd  │◄──────┤ KV watch on                │   │
│  │ A/B slot manager  │       │ EDGE_DESIRED.{uuid}        │   │
│  └───────────────────┘       │ + signed-manifest verify   │   │
│                              │ + Cosign verify            │   │
│                              └────────────────────────────┘   │
└──────────┬──────────────────────────────────────┬─────────────┘
           │                                      │
       OT NIC                                  IT NIC (egress only)
           │                                      │
           ▼                                      ▼
   PLCs / equipment              Private network → central NATS
                                 Private network → OCI registry
```

**Single-host is defensible if and only if these five conditions hold.** They are checklist items in every reference-deploy validation; failure of any one means the deploy is non-compliant.

| # | Condition | Why |
|---|---|---|
| 1 | NATS ACL on the edge user is the tightest possible — subscribe only on `EDGE_DESIRED.{its-uuid}`, publish only on its own telemetry / event / `EDGE_REPORTED` subjects. No wildcards. No request/reply. | An ACL slip undoes the entire control-plane security model. **[P5]** |
| 2 | Image references are content-addressed (digest, not tag), validated by signed manifest, verified by Cosign signature against pinned public keys. | Closes the supply-chain and registry-compromise vectors. Registry becomes untrusted byte distribution. **[P6]** |
| 3 | Bridge container is a pure NATS client. No listening sockets. Binds explicitly to the OT NIC. Drops capabilities. Read-only rootfs. Non-root user. | Eliminates the inbound attack surface on the bridge from the IT side; constrains blast radius on compromise. **[P3]** |
| 4 | Network namespaces + host firewall rules enforce OT/IT separation. Bridge container cannot reach IT NIC; Leaf cannot reach OT NIC. Verified by `nft` rules at boot. | Network namespacing is the cheap substitute for physical separation; only works if firewall enforces it. **[P3]** |
| 5 | Host kernel patching follows a documented cadence (RTO for critical CVEs: 7 days). | The kernel is now the only thing between the two containers; kernel CVE handling becomes the highest-priority edge operational discipline. **[P6]** |

**Hardware envelope** (recommended, not mandated):

| Class | Use case | CPU | RAM | Disk | Network |
|---|---|---|---|---|---|
| Small | Single line, light Sparkplug B | 4-core ARM64 or x86 | 8 GB | 128 GB NVMe | 2× 1 GbE (OT + IT) |
| Medium | Multi-line, OPC-UA + Sparkplug | 8-core x86 | 16 GB | 512 GB NVMe | 2× 1 GbE or 1× 10 GbE + 1× 1 GbE |
| Large | High-frequency telemetry, facility aggregator | 8-16 core x86 | 32 GB | 1 TB NVMe RAID-1 | 2× 10 GbE |

**Host software stack:**
- **OS:** Minimal Linux (Debian / Ubuntu Server LTS / RHEL-derivative depending on customer policy). Provisioned via Ansible (not USB cloud-init — see §3.7).
- **Container runtime:** podman + systemd. No Docker engine. No `docker.sock`. **[P6]**
- **Disk encryption:** LUKS with TPM-sealed key (where TPM 2.0 is available) or operator-keyed boot.
- **Secure boot:** enabled. Signed kernel where the customer's hardware supports it.
- **USB ports:** disabled at firmware level for production; chassis-open detection where chassis supports it.
- **Host firewall:** `nft` rules loaded at boot, declared in code, idempotent.

**Containers on the edge:**

| Container | Network namespace | Role |
|---|---|---|
| Sparkplug Bridge / OPC-UA Bridge / Modbus Bridge | OT-facing only (cannot route to IT NIC) | Protocol ingress; emits to local NATS Leaf |
| NATS Leaf Node | IT-facing only (cannot route to OT NIC) | JetStream buffer; outbound WSS:443 to Enterprise NATS |
| Edge Update Agent | IT-facing only | Watches `EDGE_DESIRED.{uuid}`; validates signed manifest; orchestrates podman + systemd update flow |
| Edge Reports (optional) | IT-facing only | Local Streamlit dashboard for facility staff during connectivity loss |

All containers run as non-root, with capability allow-lists, no host network sharing, and read-only root filesystems where possible.

#### 3.4.2 Dual-host reference variant (defense / aerospace / IDS-visibility customers)

Two edge IPCs per facility, with the bridge on an OT-side host and the leaf + update agent on an IT-side host. Same image set as single-host; deployment mode is a topology choice, not a software change.

```
┌────────────────────────────┐         ┌────────────────────────────┐
│  OT-side IPC               │         │  IT-side IPC               │
│                            │         │                            │
│  Bridge container          │         │  NATS Leaf container       │
│  binds OT NIC              │         │  binds IT NIC (egress 443) │
│         ▲                  │         │         ▲                  │
│         │                  │         │         │                  │
│  Update Agent (its own)    │         │  Update Agent (its own)    │
│  Host firewall: outbound   │ ◄──mTLS─►│  Host firewall: inbound    │
│  only to IT-side IPC :4222 │         │  from OT-side IPC :4222    │
└─────────┬──────────────────┘         │  only                      │
          │                            └─────────┬──────────────────┘
       OT NIC                                    │
          │                                  IT NIC (egress only)
          ▼                                      │
  PLCs / equipment                               ▼
                                  Private network → central NATS
                                  Private network → OCI registry
```

**When to recommend this variant:**

1. **Customer's existing OT IDS** (Nozomi, Claroty, Dragos) needs cross-host visibility. Those tools see network traffic, not intra-host container traffic across Linux network namespaces.
2. **Customer's compliance auditor wants physical separation as evidence.** Some IEC 62443-3-3 SL-2 interpretations prefer demonstrable hardware-level segregation over namespace-based isolation.
3. **Customer policy enforces independent patch cadences** for OT and IT systems. Two hosts allow each to follow its own discipline without operational compromise.

**Additional controls beyond the single-host five:**

| Control | Detail |
|---|---|
| Dedicated VLAN trunk | Inter-host link runs on a dedicated VLAN, not the OT or IT VLAN. |
| Inter-host firewall | OT-side host accepts inbound only from IT-side host's specific IP on the NATS port (4222 or whatever is configured); IT-side host accepts inbound only from OT-side host's IP. Customer's network firewall enforces it as defense in depth. |
| Inter-host mTLS | NATS leaf ↔ bridge link is mTLS-mutual; certs distinct from the central-NATS certs. |
| Two Update Agents | Each host runs its own Update Agent independently. Each subscribes to its own `EDGE_DESIRED.{uuid}` key. |
| Customer IDS placement | Customer's OT IDS sits on the inter-host VLAN trunk for visibility. |

**Cost:** approximately €800–1,500 additional hardware per facility plus configuration overhead. For defense / aerospace customers this is rounding error against the deal economics.

The architecture supports both modes from the same image set; switching mode is a deployment topology + Ansible playbook choice, not a software change.

#### 3.4.3 High-assurance variant (data diode)

Documented in §3.x of `defense-aerospace-roadmap.md` Stage 4. Not built proactively; documented as available scope for sites with classified-adjacent data or hard regulatory firewalls (some NASA programs, some UK MoD work). Data diode hardware (Owl Cyber Defense, Fox-IT, Advenica) replaces the inter-host bidirectional link with a unidirectional one. Config updates happen via signed bundles delivered out-of-band.

### 3.5 Protocol matrix

Per the defense-aerospace roadmap §3.5 / `arangodb-migration.md`-adjacent thinking, each protocol has an explicit security stance:

| Protocol | Use | Security stance | Status |
|---|---|---|---|
| **Sparkplug B (MQTT 3.1.1)** | Modern equipment with Sparkplug-aware nodes | NATS JWT auth + WSS TLS on the bridge → cluster hop; raw MQTT side handled within OT VLAN | **Shipping** (May 15 demo) |
| **OPC-UA** | PLC/equipment with OPC-UA servers (Siemens, Rockwell, B&R, Beckhoff) | `SignAndEncrypt` security mode **mandatory**; config schema rejects `None` mode at startup; user-token auth or X.509 client cert | **Roadmap — Stage 1** |
| **Modbus TCP** | Legacy equipment, no native security | Allowed *only* within OT VLAN; wrapped in IPsec or stunnel when crossing any L3 boundary; warning banner in config | **Roadmap — Stage 2** |
| **EtherNet/IP (CIP)** | Rockwell-heavy plants | Read-only by default; bridge reads tags via PCCC or CIP explicit messaging | **Roadmap — Stage 2** |
| **S7 (Siemens proprietary)** | Older Siemens PLCs without OPC-UA UA-Server | Same OT-VLAN constraint as Modbus | **Roadmap — Stage 2/3** |
| **MQTT (non-Sparkplug)** | Generic IoT devices, building management | Per-tenant ACLs, mTLS where device supports it | **Roadmap — Stage 3** |

For each protocol, a separate ADR will document the bridge implementation, security defaults, supported PLC vendor matrix, and known limitations.

### 3.6 Multi-region federation

For customers with multiple facilities spread across regulatory regions (the tier-1 defense/aerospace profile), a single global Enterprise tier is not appropriate. Federation architecture:

**Regional Enterprise instances.** Typically 3 (NA, EU, APAC) — exact count driven by customer's facility distribution and regulatory map. Each is a self-contained Progress deployment.

**Data-classification-aware replication.** Cross-region data flow is governed by a per-class policy:

| Class | Example | Replication policy |
|---|---|---|
| **Public / aggregate** | Cross-site OEE KPIs, scrap rate trends | Replicated freely across regions; aggregated and visible globally |
| **Operational (internal)** | Production events, work order state, telemetry | Replicated to disaster-recovery region only; not visible cross-region by default |
| **Controlled (export)** | ITAR / EAR / CGP / SCOMET-scoped technical data, classified-program telemetry | **Stays in source region.** No cross-region replication. Federated KPIs derived from anonymised aggregates only. |
| **Personal data (GDPR / DPDP / PIPEDA)** | Operator identifiers, badge scans, biometric login | Stays in source region; replicated only with documented lawful basis |

The policy is enforced at the NATS stream / subject level: streams tagged with a data-classification attribute are only mirrored to regions whitelisted for that class. Violation attempts are themselves audit events.

This addresses the four-regime regulatory exposure (US ITAR/DFARS, UK MoD/GDPR, Canada CGP/PIPEDA, India SCOMET/DPDP) head-on. **No customer of meaningful size will accept a single-region "global cloud" model — federation is a Day-1 architectural commitment.**

### 3.7 Provisioning and identity

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

**Revocation:** documented procedure with RTO < 1 hour. Account JWT carries a `revocations` field maintained centrally. Revocation list propagation tested as part of DR drills.

### 3.8 Security model summary

| Concern | Posture |
|---|---|
| **Transport** | mTLS end-to-end (NATS, API, DB, Prefect, internal HTTP). External edge: Traefik + Let's Encrypt or customer-CA-issued cert (see `km/architecture/https.md`). Internal: cert-manager + internal CA (offline root + online intermediate). |
| **Identity** | Decentralised NATS JWT (Operator → Account → User) + Progress-API JWT (Ed25519 post-Stage-1; HS256 today per `backend/api/utils/auth.py`). |
| **Revocation** | NATS revocation lists + Progress `Token.revoked` collection. Documented RTO. |
| **Audit trail** | Event-sourced platform events (immutable in Postgres post-ADR-0011); structured audit events on NATS `audit.*`; `pgAudit` on the DB. NIST 800-171 AU-family coverage. |
| **Encryption at rest** | LUKS at host level; Postgres TDE (Cybertec / Percona) for customers requiring FIPS-validated modules in Stage 3. |
| **Supply chain** | Cosign-signed images; SBOM (syft) per image; signing key in sealed file (Stage 1) → HSM (Stage 3). SLSA L3 target in Stage 3. |
| **Vulnerability management** | Dependabot + Renovate + weekly image vuln scan; public CVD policy from Stage 2. |
| **Multi-tenancy isolation** | NATS account-level isolation between customers in Managed Cloud; documented pen-test scope from Stage 1. |

### 3.9 High availability and disaster recovery

**HA topology (on-prem, customer-deployed):**

- **NATS:** 3-node JetStream cluster with RAFT quorum; R=3 replication on critical streams.
- **PostgreSQL + Timescale:** Patroni-managed primary + sync replica + async replica; etcd for consensus; pgBackRest for backups with WAL archiving to S3 Object Lock (or customer-equivalent immutable storage).
- **Progress API:** stateless; 2+ instances behind Traefik HA pair.
- **Traefik:** HA pair with VRRP / floating IP, or DNS-based failover for cross-zone deployments.
- **Object storage / OCI registry:** customer-deployed (Gitea + S3-backed storage, or Harbor + customer storage).

**Documented targets:** RPO 1 minute, RTO 5 minutes. Stage 2 deliverable.

**DR:**
- Quarterly restore drill mandated by Stage 2.
- Cross-region failover documented as runbook; tested annually from Stage 2.
- Backup immutability via Object Lock (ransomware-resilient).

Managed Cloud uses the same primitives, operated by Progress, with documented multi-tenant isolation and per-customer key custody.

---

## 4. Data lifecycle

### 4.1 Telemetry path

```
PLC / Equipment
   │  (Sparkplug B / OPC-UA / Modbus)
   ▼
Edge Protocol Bridge
   │  normalisation, alias resolution, quality flags (good/stale/bad)
   ▼
Local NATS Leaf (JetStream buffer)
   │  persistent buffer; survives connectivity loss
   ▼
Regional NATS Cluster (over WSS:443, mTLS)
   │
   ├──► Timescale historian (high-cardinality time-series, downsampled per ADR-0005)
   ├──► Last-value KV (`SPARKPLUG_LAST_VALUES`) for fast UI / report reads
   ├──► Event-class triggers (threshold-cross → Issue, gap → audit event)
   └──► Streaming-processing layer (Bytewax, post-demo per ADR-0009)
```

### 4.2 Platform-event path (transactional)

```
HTTP request / UI action / bridge automation
   │
   ▼
FastAPI endpoint  (backend/api/endpoints/)
   │  Pydantic validation
   ▼
Event object instantiated  (backend/api/events/, 50+ event types)
   │
   ▼
Event.save() → pre_processing() → apply() → store_event()
   │  ArangoDB transaction (today)  →  PostgreSQL transaction (post-ADR-0011)
   ▼
Commit OR abort  (atomic)
   │
   ▼
Side-effect fan-out via Managers + NATS subjects (events.*)
   │
   ▼
Downstream consumers (notifications, automations, reports)
```

The event sourcing model is what makes the AS9100D 7.5 + 8.5.2 evidence story essentially free — every state-changing operation is captured as an immutable event before it becomes a state mutation, with the transaction guaranteeing both halves succeed or neither does.

### 4.3 Audit + compliance evidence

| Standard | Control family | How Progress evidences it |
|---|---|---|
| **AS9100D 7.5** (documented information) | Records | Event store is the system of record; all events immutable, queryable, exportable |
| **AS9100D 8.5.2** (identification & traceability) | Genealogy | Serial graph (`contains` edges, see ADR-0011) + event history per serial = full as-built/as-maintained chain |
| **NIST 800-171 AU-2/AU-3** | Auditable events | `audit.*` NATS subjects + `pgAudit` + platform event store |
| **IEC 62443-3-3 SR 2.8** | Auditable events | Same as above |
| **NIS2 Article 21** | Incident handling | Incident response runbook (Stage 2) + audit-trail forensic preservation |
| **GDPR Art. 30** | Records of processing | Documented data classification + replication policy per §3.6 |

A dedicated `km/compliance/matrix.md` (Stage 0 deliverable per defense roadmap) maps every applicable control to evidence pointers in the codebase / deployment.

---

## 5. Integration touch points

Progress is the substrate; it must integrate cleanly with the customer's existing IT estate.

**Identity providers:**
- LDAP / Active Directory for user authentication (federated via OIDC where customer has an IdP like Azure AD, Okta, Keycloak)
- SCIM provisioning for user lifecycle (Stage 2+)

**Enterprise systems:**
- **ERP** (SAP, Oracle, IFS, Infor): bidirectional integration via REST endpoints + webhook events for production-order sync, BOM sync, inventory transactions. No direct DB-to-DB.
- **MES** (where one exists at facility level): typically Progress *is* the MES, but coexistence with legacy MES via event subscriptions is supported.
- **QMS** (where separate): NCR / Issue linkage via API.
- **PLM / CAD** (Teamcenter, Windchill): BOM and part-master sync via scheduled extract or PLM-side webhook.

**Security / SOC:**
- **SIEM:** syslog forwarder (RFC 5424 / 5425), Common Event Format (CEF), or OCSF-compliant event export from `audit.*` subjects to customer's Splunk / Sentinel / QRadar / Elastic SOC.
- **IDS/IPS:** Progress does not provide network IDS; customer's existing OT IDS (Nozomi, Claroty, Dragos) sits passively on the OT VLAN.
- **Vulnerability management:** SBOMs published per release; integration with customer's vuln scanner via standard SPDX / CycloneDX formats.

**Analytics estate:**
- Customers running their own data lake (Snowflake, Databricks, BigQuery): Progress exports via Debezium-style CDC or scheduled bulk export; data residency rules from §3.6 apply.

---

## 6. Open questions / unresolved

Listed because pretending they're solved would be dishonest. Resolution path noted.

1. **Edge OTA orchestrator implementation** — write our own thin updater on podman+systemd vs adopt Mender / RAUC. ADR pending; depends on Stage 1 spike.
2. **PKI substrate** — internal cert-manager + our CA vs customer-issued certs from their CA vs hybrid. Likely customer-driven per deployment.
3. **AGE vs recursive-CTE** for graph queries on Postgres — per ADR-0011 spike (Stage 0.5).
4. **Bytewax adoption timing** — per ADR-0009 (post-demo). Affects whether streaming processing happens in-bridge (today) or in a separate stream-processing tier (future).
5. **Reports/UI strategy at scale** — Streamlit is right for current customer profile; tier-1 customers will want full-featured BI integration (PowerBI / Tableau / Grafana Enterprise). Plan TBD.
6. **Commercial-support function shape** — see `defense-aerospace-roadmap.md` §5 + companion conversation on solo-maintainer positioning at tier-1 scale.
7. **Live-config-without-redeploy workflow** — the immutable-infrastructure stance (§3.3) means every behaviour change requires a new signed image. This is a security feature but an operational tension for customers used to runtime config knobs. Resolution path: invest in a CI/CD pipeline that makes "change threshold → new image → new deploy" feel like 90 seconds end-to-end; document the workflow as a feature, not a limitation. Stage 2 deliverable. Where customers reject immutable infrastructure outright, document the trade-off frankly and let the customer choose — do not add a runtime-config back-channel that undermines the control-plane security model.

---

## 7. Reference list

**Internal:**
- `km/strategy/defense-aerospace-roadmap.md` — security / compliance posture roadmap
- `km/strategy/arangodb-migration.md` — substrate migration analysis
- `km/architecture/https.md` — Traefik / TLS setup
- `km/architecture/sparkplug.md` — Sparkplug B integration details
- `km/auth/tokens.md` — current API token lifecycle
- `.planning/workstreams/sparkplug-demo/decisions/0002-nats-subject-taxonomy.md`
- `.planning/workstreams/sparkplug-demo/decisions/0005-timescale-schema-and-downsampling.md`
- `.planning/workstreams/sparkplug-demo/decisions/0008-natsmqtt-subject-mapping.md`
- `.planning/workstreams/sparkplug-demo/decisions/0009-stream-processing-framework.md`
- `.planning/workstreams/sparkplug-demo/decisions/0010-hardcoded-automation-for-v1-demo.md`
- `.planning/workstreams/sparkplug-demo/decisions/0011-database-substrate.md`
- `.planning/workstreams/sparkplug-demo/decisions/0012-graph-query-substrate.md`
- `.planning/workstreams/sparkplug-demo/STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md`

**External standards:**
- ISA-95 / IEC 62264 — Enterprise-Control System Integration
- Sparkplug B specification v3.0 — Eclipse Foundation
- OPC-UA Part 2 — Security Model
- IEC 62443-3-3 — System security requirements
- NIST SP 800-171 r3 — Protecting CUI in Nonfederal Systems
- AS9100D — Quality Management Systems (aerospace)

---

## 8. Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | 2026-05-21 | CTO | Initial draft; supersedes external "IIoT Edge-to-Cloud Architecture Spec v1.0" by addressing security, supply-chain, HA, and federation gaps surfaced in the May 2026 architectural review. |
