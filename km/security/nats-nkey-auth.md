# NATS NKey/JWT Authentication & Bring-up

How decentralized NATS auth actually works on the Progress IIoT substrate, and the operator runbook for standing up the hub, edge leaf nodes, and clients. This is the mechanism + provisioning companion that [`iiot-security.md`](./iiot-security.md) §5 references but does not spell out.

**Companion documents:**
- [`iiot-security.md`](./iiot-security.md) — owns the identity *hierarchy* (§5), the edge ACL *intent* (§3.3), enrollment, revocation policy
- [`../architecture/iiot-architecture.md`](../architecture/iiot-architecture.md) — topology, data plane, leaf/edge deployment
- [`tokens.md`](./tokens.md) — the *separate* Progress-API JWT (HS256 today, Ed25519 roadmap). Not the same as NATS auth.
- Skill: `nats:auth` (NKeys, JWTs, accounts, permissions reference)

> **Scope note.** This doc is the *target model*. Decentralized JWT auth is not yet wired into the live demo stack (which still uses simpler NATS auth); the staged path to it is in [`../strategy/defense-aerospace-roadmap.md`](../strategy/defense-aerospace-roadmap.md).

---

## 1. NKey vs JWT — what each actually is

An **NKey** is an Ed25519 keypair with NATS-specific base32 encoding (type-prefix byte + 32-byte key + CRC16). The crypto is vanilla Ed25519; only the encoding is NATS-specific.

- **Public key = the identity.** It's what the server knows you by. Prefixes: `O` operator, `A` account, `U` user, `S` server.
- **Private key = the "seed"** (prefix `S` + role, e.g. `SU`, `SA`, `SO`). The seed never leaves the holder. The server stores **no secret** — there is nothing to steal server-side. This is the core advantage over tokens/passwords.

Critically: **an NKey carries no permissions.** It is pure identity. Authorization lives in one of two places — and which one is the whole architectural fork:

| Mode | Identity lives | Authz lives | Scaling |
|------|----------------|-------------|---------|
| NKey-only (static) | `nkey: U…` in `nats-server.conf` | server config, keyed by pubkey | every key in server config → centralized |
| **NKey + JWT (decentralized)** | user pubkey embedded in a signed JWT | claims *inside* the JWT | server pins only the operator key → scales to N tenants |

Progress uses the **decentralized** model (`iiot-security.md` §6: "Decentralised NATS JWT (Operator → Account → User)"). Everything below assumes it.

## 2. The signing chain

Each entity is a JWT whose **subject** is that entity's NKey public key, **signed by the parent's NKey seed**:

```
Operator NKey (O…)                      ← root of trust, pinned in every hub server
  signs → Account JWT  (sub: A…, iss: O…)   ← account limits, exports/imports, revocations
            Account NKey (A…)
              signs → User JWT (sub: U…, iss: A…)
                        + permission claims  ← the ACL (pub/sub allow-deny, limits, exp)
```

- **Operator JWT** is pinned directly in `nats-server.conf` (`operator: operator.jwt`). The *only* key the server trusts a priori; everything else chains back to it.
- **Account JWT** is signed by the operator seed; holds account limits, JetStream quotas, exports/imports, and the **revocation list**.
- **User JWT** is signed by the account seed; holds the permission set the server enforces.

### Signing keys vs root keys (what makes the custody model work)

Operators and accounts can hold **separate signing keys** distinct from their root identity key. You sign with the signing key and keep the root key offline/HSM. This is the mechanism behind `iiot-security.md` §5's "signing key offline; HSM target":

- Operator **root** NKey → offline/HSM; only ever adds/rotates operator signing keys.
- Operator **signing** key → mints customer account JWTs.
- Account **root** NKey → offline, customer custody.
- Facility **signing** key → lives at the enrollment service; mints device user JWTs at provisioning.

Compromising a signing key lets you mint within that scope but is revocable without rotating the root — the property §3.1's two-person/separation-of-duties argument leans on.

## 3. How a client authenticates (the connect handshake)

No secret transits the wire. It's a nonce challenge:

```
1. Client opens TCP/TLS. Server sends INFO { nonce: <random> }
2. Client signs the nonce with its user SEED and sends:
   CONNECT { "jwt": "<userJWT>", "sig": "<base64(sign(nonce))>" }
3. Server verifies, in order:
   a. userJWT signed by an account it knows (sub == iss of userJWT)
   b. that account JWT signed by the pinned operator
   c. account not expired / not in operator revocations
   d. user pubkey not in account.revocations, and iat >= any revoke timestamp
   e. sig verifies against userJWT.sub (the user public key)
4. Server loads permission claims from userJWT → enforces them for the session
```

Step 3e proves possession of the private seed; 3a–3b prove legitimate issuance; 3d is revocation. All offline crypto — no DB lookup on the hot path. The `.creds` file a service loads is just **userJWT + user seed** concatenated.

**Distribution subtlety:** user JWTs are *never* pushed to the server — the client presents its own at connect. Only **account JWTs** must be server-side, via the **resolver**:

| Resolver | Use |
|----------|-----|
| `mem` | accounts static in config (small/fixed tenant set) |
| `full` (nats-resolver) | servers persist account JWTs to a dir + gossip cluster-wide; `nsc push` uploads. **What Progress wants** — onboard a customer without restarting the hub. |
| URL | fetch from an external account server |

## 4. Authorization = the user JWT's permission claims

The §3.3 "tightest possible grant" *is* the permission block minted into the bridge's user JWT:

```jsonc
// claims inside acme.vicenza.line3.bridge1's user JWT
"nats": {
  "pub": { "allow": ["telemetry.acme.vicenza.line3.>", "EDGE_REPORTED.<uuid>"] },
  "sub": { "allow": ["EDGE_DESIRED.<uuid>"] },
  // NO _INBOX.>  → no request/reply (matches §3.3)
  "subs": 32, "data": 1048576,           // subscription / payload caps
  "type": ["leafnode"], "src": ["10.20.0.0/24"]  // conn-type / source-CIDR pins
}
```

Two load-bearing facts:

- **Default = allow-all.** A user with empty permissions can pub/sub `>`. You must explicitly allow-list. The "automated ACL-diff on every deploy" (§3.3) is checking that these minted `allow` claims match intent.
- **The ACL is baked into a signed artifact at issuance.** A mistake isn't a hot-patchable config line — fixing it means **re-mint + redeploy** the credential. This is *why* "an ACL slip undoes the entire security model."

KV bucket ACLs (§3.4) are the same mechanism: KV is subject-backed (`$KV.<bucket>.>`), so "EDGE_DESIRED is CI-write / edge-read-only" decomposes into pub/sub allow-lists on those subjects in the respective accounts' user JWTs.

---

## 5. Operator bring-up runbook

Topology (three tiers):

```
HUB (main cluster, cloud)         ← operator JWT pinned, full resolver
  ▲ outbound WSS:443 leaf conn     [P4]
LEAF (edge IPC nats-server)        ← JetStream store-and-forward, leaf.creds
  ▲ localhost
CLIENTS (bridge, sim, update-agent, API, CI)  ← pure NATS clients, per-service .creds
```

All driven with `nsc`.

### 5.0 Trust root (one-time, offline — guard the output)

```bash
# Operator WITH a signing key + system account. --generate-signing-key is non-negotiable:
# it lets the root key go offline.
nsc add operator --generate-signing-key --sys --name Progress

# Pin the resolver URL the hub serves account JWTs from (nsc + clients push/pull here).
nsc edit operator --account-jwt-server-url nats://hub.progress.example.com:4222
nsc edit operator --sk generate          # add per-purpose signers as needed
```

Then **physically remove the operator root seed** from the working keystore → HSM/sealed file (§5 "HSM target in Stage 3"). Day-to-day issuance only ever touches signing keys. Artifacts that matter: `operator.jwt` (pinned into every hub server) + the SYS account.

### 5.1 Hub (main) nodes

```bash
nsc generate config --nats-resolver > /etc/nats/resolver.conf
```

```conf
# /etc/nats/hub.conf
operator: /etc/nats/operator.jwt
system_account: <SYS account pubkey>
include resolver.conf          # resolver: { type: full, dir: "./jwt", interval: "2m", allow_delete: false }

tls { cert_file: "...", key_file: "...", ca_file: "..." }              # client port — TLS mandatory [P5]
cluster { name: progress-hub, port: 6222, tls { ... }, routes: [ ... ] }

leafnodes {                    # edge dials in here; exposed wss:443 via Traefik [P4]
  port: 7422
  tls { cert_file: "...", key_file: "...", ca_file: "..." }
}
```

Start the cluster. It trusts the operator but knows **zero accounts** — every connect fails until accounts are pushed. Expected.

### 5.2 Per-customer account (repeat per customer / per facility)

```bash
nsc add account acme-aerospace
nsc edit account acme-aerospace --sk generate          # facility/account signing key
nsc edit account acme-aerospace --js-mem-storage 1G --js-disk-storage 50G --js-streams 100
nsc push -a acme-aerospace                             # publish to hub resolver — NO hub restart
```

Make per-facility accounts (`acme-vicenza`) separate, not one big `acme` — gives §5's facility-scoped revocation isolation. The account signing key is what lives at the **enrollment service** and mints device user JWTs.

### 5.3 Leaf nodes (edge IPCs)

Two separate credentials at the edge — keep them distinct:

**(a) Leaf connection credential** — a user the leaf uses to authenticate its outbound link:

```bash
nsc add user --account acme-aerospace vicenza-line3-leaf
nsc edit user vicenza-line3-leaf --account acme-aerospace \
  --allow-pub "telemetry.acme.vicenza.line3.>,events.acme.vicenza.line3.>,EDGE_REPORTED.<uuid>" \
  --allow-sub "EDGE_DESIRED.<uuid>"
nsc generate creds --account acme-aerospace --name vicenza-line3-leaf > leaf.creds
```

**(b) Edge `nats-server` config** — local JetStream domain for store-and-forward, dials hub outbound:

```conf
# /etc/progress/edge.conf  (on the IPC)
jetstream { domain: edge, store_dir: "/var/lib/nats" }   # distinct domain → edge & hub streams don't collide
leafnodes {
  remotes: [ { url: "wss://hub.progress.example.com:443", credentials: "/etc/progress/leaf.creds" } ]
}
host: 127.0.0.1                # local client port — localhost only
tls { ... }
```

The edge server is **outbound-only** [P4] — `remotes` only, no listener facing the IT network. Subjects it publishes surface on the hub *inside the `acme-aerospace` account namespace* (the leaf creds' account). `domain: edge` gives store-and-forward across WAN drops.

> **Note on §4 wording.** `iiot-security.md` §4 says "the bridge is a pure NATS client" — correct, but the bridge is a client *of the local leaf server*. The edge box **runs a `nats-server` (leaf)**; the bridge dials localhost, not the hub directly. The `jetstream { domain: edge }` line is what gives the store-and-forward buffer.

### 5.4 Clients (bridge, sim, update-agent, API, CI)

```bash
# Edge bridge — same account as the leaf
nsc add user --account acme-aerospace vicenza-line3-bridge1
nsc edit user vicenza-line3-bridge1 --account acme-aerospace \
  --allow-pub "telemetry.acme.vicenza.line3.>,EDGE_REPORTED.<uuid>" \
  --allow-sub "EDGE_DESIRED.<uuid>"          # no _INBOX.> → no request/reply
nsc generate creds --account acme-aerospace --name vicenza-line3-bridge1 > bridge1.creds

# CI / deployments — SEPARATE account, can write EDGE_DESIRED, NOT EDGE_REPORTED (§3.4)
nsc add user --account progress-ci deployer
nsc edit user deployer --account progress-ci --allow-pub "EDGE_DESIRED.>" --deny-pub "EDGE_REPORTED.>"
```

Client loads the creds:

```python
await nats.connect("tls://127.0.0.1:4222", user_credentials="/etc/progress/bridge1.creds")
```

```bash
nats --creds bridge1.creds pub telemetry.acme.vicenza.line3.temp 21.4
```

### 5.5 Startup order + verification

Accounts must exist on the resolver **before** anything that uses them connects:

```
1. Hub cluster up         → trusts operator, knows no accounts yet
2. nsc push -A            → push SYS + all customer/CI accounts to resolver
3. Edge leaf nodes start  → dial wss:443, authenticate with leaf.creds
4. Edge clients start     → bridge/sim/update-agent connect to localhost leaf
5. Hub-side services      → API/managers connect with their creds
```

Verify each layer:

```bash
nsc describe account acme-aerospace                              # signing keys, limits, revocations
nats --creds bridge1.creds pub telemetry.acme.vicenza.line3.test ok    # client → leaf
nats --creds hubmon.creds sub "telemetry.acme.>"                # confirm leaf forwarding to hub
nats server check connection                                    # leaf link health
# Watch $SYS.ACCOUNT.*.LEAFNODE.CONNECT (SYS-account monitor user) for leaf up + auth failures
```

## 6. Day-2: rotation, revocation, onboarding

| Task | Command(s) |
|------|-----------|
| Onboard a customer | `nsc add account X` → `nsc push -a X` (**no hub restart** — property of the `full` resolver) |
| Issue a device | enrollment service mints user JWT with facility signing key (§5) |
| Re-scope a client's ACL | `nsc edit user … --allow-pub …` → **re-issue creds, redeploy** (claims are baked in) |
| Revoke a device | `nsc revoke add-user -a X --name dev1` → `nsc push -a X` (RTO = push + resolver `interval`) |
| Revoke a facility | revoke/replace that facility's account JWT — siblings untouched |
| Rotate operator signer | `nsc edit operator --sk generate`, retire old `--rm-sk`, never touches root |

## 7. Open design points

1. **Device-generated seed.** §5 says the enrollment service issues "the device's NKEY/JWT," implying it generates the keypair and ships both halves. Best practice is the inverse: the **device generates its own seed locally and transmits only its public key**; the service mints a JWT binding that pubkey and never sees the private seed. Preserves the "private key never leaves the holder" invariant through provisioning. Cheap to adopt, strengthens the §3.1 compromise argument.
2. **Long-lived vs short-`exp` credentials.** IIoT services argue for no/long `exp` + reliance on revocation lists; defense-in-depth argues for short `exp` + automatic re-mint (rotation through the enrollment path). Can't have both cheaply — pick per customer posture and document. Pairs with `iiot-security.md` §8.

---

## 8. Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | 2026-06-16 | — | Created from auth deep-dive: NKey/JWT mechanism, signing chain, connect handshake, ACL-as-JWT-claims, and the operator bring-up runbook (hub / leaf / clients). Companion to `iiot-security.md` §5/§3.3. |
