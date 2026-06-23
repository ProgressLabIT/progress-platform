# Aerospace Mill Live Twin — Rehearsal Runbook

**Audience:** demo operator · **Companion doc:** [Demo Brief](aerospace-mill-twin-demo.md)
**DEMO-01 loop:** raise tool-wear **and** feed/tooth → spindle torque crosses **45 N·m** → ~5 s dwell → a linked Issue appears in the Progress Issues view.

> This runbook is the operational checklist. For narrative context (why the demo matters, the machine, the signal, the beats in prose form) see the Demo Brief above.

## Two deploy targets — read first


|                     | Local rehearsal                                        | Customer-facing server                                                 |
| ------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------- |
| Orchestrator        | `docker compose`                                       | **Docker Swarm** (`docker stack deploy`)                               |
| Host                | `progress.localhost` (http)                            | `demo.progresslab.it` (https)                                          |
| NATS WS to panel    | direct `ws://localhost:8090` (`dev.yaml` publishes it) | `wss://<host>/nats` via Traefik (`nats-ws.yaml` route → `broker:8090`) |
| `demo_twin` `:8001` | published (local only)                                 | **not** published — reached via `/twin` route                          |
| Live config files   | you must seed the external `config` volume yourself    | provisioned at `/opt/progress/config/`                                 |


The two paths share the same images and the same **Issue-binding mechanism** (below). Differences are called out per-step.

---

## Issue binding — where the demo's keys actually live (READ THIS)

`mill_automation` builds each Issue from four keys: `issue_type_key` + the `serial` / `work_order` / `operation` link keys. **The live source of all four is the JSON file `mill_automation.json`** in the shared `config` volume (`/config/mill_automation.json` inside the container, `/opt/progress/config/mill_automation.json` on the server). It is **re-read on every Issue fire — no restart needed** (`config.py:69-74`, `issue_client.py:38-69,106`).

**Precedence (`issue_client.py:49,65-68`):** for each key, the JSON value wins **if it is a non-empty string**; otherwise the `MILL_AUTO_`* env var (from `.env`) is used as a fallback. Env changes are read only at container start (recreate required); JSON edits are live.

> ⚠️ **Committed-state footgun.** The repo ships `deploy/compose/.env` with real numeric keys (`MILL_AUTO_LINKED_SERIAL_KEY=74430428`, …) but `deploy/config/mill_automation.json` with **non-empty placeholder** links (`WING-DEMO-001`, …). Because non-empty JSON wins, the placeholders **silently override** the numeric env keys, so the Issue links to `WING-DEMO-001`/`WO-DEMO-001`/`OP-DEMO-001` regardless of `.env`. **Reconcile them:** put the real seeded `_key`s in `mill_automation.json` (or blank the JSON link fields to fall back to `.env`).

> **`twinConfig.js` `WO_LINKS` does NOT affect the binding.** It is display-only — `controls.js:injectWoLinks` writes those keys into the panel's WO-ticket text (`mill_automation` never reads it; the panel never POSTs it). Match it to `mill_automation.json` only so the panel *shows* the same IDs the Issue links to; a mismatch is cosmetic, not a failure.

---

## Prerequisites

- Docker Desktop running with at least 4 GB RAM available.
- Repo checkout at `.worktrees/mill-twin` with the Phase 5 overlay committed.
- Both demo images built (see below). These are NOT pulled from a registry.
- Issue binding set in `mill_automation.json` (see "Demo-seed coordination" — do this FIRST).
- JWT token file minted to disk (see "Mint the automation JWT" — do this BEFORE bringing the stack up; the `mill_automation_jwt` secret fails the deploy if the file is absent).
- **Local only:** the external `config` and `reports` volumes created and seeded (see "Run it — local").

**Build both images (run from repo root):**

```bash
docker build -t progress-demo-twin:dev \
  -f demos/mill_twin/demo_twin/Dockerfile demos/mill_twin/

docker build -t progress-mill-automation:dev \
  -f demos/mill_twin/mill_automation/Dockerfile demos/mill_twin/
```

These only need re-building when the source changes. Safe to skip if images are already present (`docker images | grep progress-`).

---

## Demo-seed coordination (do this first — the rehearsal validates it)

### 1. Set a valid IssueType key

If `issue_type_key` is empty in **both** `mill_automation.json` and `MILL_AUTO_ISSUE_TYPE_KEY`, the automation **logs `issue fire skipped … no issue_type_key` and skips firing** — no Issue, no HTTP POST, **no 422** (`issue_client.py:106-114`). (The committed `.env` ships `MILL_AUTO_ISSUE_TYPE_KEY=3534068`, so the env fallback fires today — but that `_key` is environment-specific; confirm it exists in *your* DB.)

**Find a valid IssueType `_key`** (base Progress stack must be up):

```bash
curl -s http://progress.localhost/api/issue-type | jq '[.[] | {_key, name}]'
```

Pick an equipment-anomaly or process-anomaly IssueType `_key`, then set it as the **live** value:

```bash
# deploy/config/mill_automation.json  (re-read on every fire — no restart)
#   "issue_type_key": "<the _key from the query above>"
```

`MILL_AUTO_ISSUE_TYPE_KEY` in `.env` is only the fallback used when the JSON key is blank; changing `.env` requires `up -d --force-recreate mill_automation`.

If no IssueType exists, create one via `POST /api/issue-type` (`collaboration.py:77`). Note this is a **direct collection insert, not event-sourced** — only the Issue itself (`ISSUE_CREATED`) goes through the event pipeline. Use the API rather than a manual `arangosh` insert.

### 2. Demo WO / Serial / Operation must exist in local Progress

`mill_automation` links every Issue to these three records (`issue_client.py:80-85`):


| Binding key (`mill_automation.json`) | `.env` fallback                   | Must exist as                                                    |
| ------------------------------------ | --------------------------------- | ---------------------------------------------------------------- |
| `work_order`                         | `MILL_AUTO_LINKED_WORK_ORDER_KEY` | `WorkOrder` `_key`                                               |
| `serial`                             | `MILL_AUTO_LINKED_SERIAL_KEY`     | `**Serial`** `_key` (collection is `Serial`, not `SerialNumber`) |
| `operation`                          | `MILL_AUTO_LINKED_OPERATION_KEY`  | `Operation` `_key`                                               |


**Verify they exist:**

```bash
curl -s http://progress.localhost/api/work-order/WO-DEMO-001 | jq ._key
curl -s http://progress.localhost/api/serial/WING-DEMO-001    | jq ._key
# No GET-by-key route for Operation — check the list endpoint:
curl -s http://progress.localhost/api/operation | jq '.[]? | select(._key=="OP-DEMO-001") | ._key'
```

If they do not exist, create them via the Progress API (event-sourced — never insert directly into ArangoDB). Then set the **actual seeded `_key`s** in `mill_automation.json` (`serial` / `work_order` / `operation`) — that is what the Issue links to. Per the precedence note above, editing only `.env` has no effect while the JSON link fields are non-empty. (`twinConfig.js` `WO_LINKS` only changes what the panel displays — match it for a coherent demo, but it is not part of the binding.)

---

## Mint the automation JWT

`mill_automation` reads its JWT from a Docker **secret** named `mill_automation_jwt`, mounted read-only at `/run/secrets/mill_automation_jwt` (mode `0400`) inside the container (`mill-twin.yaml:40-42,132-134`; `config.py:31`). The secret's source is a host file — **it must exist before the stack comes up** or the deploy fails immediately.

```bash
# secrets dir — the compose secret defaults to ./secrets; .env sets PROGRESS_SECRETS_DIR
# to an absolute path. Use whatever PROGRESS_SECRETS_DIR points at.
mkdir -p "${PROGRESS_SECRETS_DIR:-./secrets}"

# Mint a 24-hour session token from the local Progress API
# (base stack must be up; substitute cadmin's password if different)
curl -s -X POST http://progress.localhost/api/auth \
  -d "username=cadmin&password=demoadmin1" \
  | jq -r '.access_token' \
  > "${PROGRESS_SECRETS_DIR:-./secrets}/mill-automation.token"

chmod 0600 "${PROGRESS_SECRETS_DIR:-./secrets}/mill-automation.token"
wc -c "${PROGRESS_SECRETS_DIR:-./secrets}/mill-automation.token"
```

> **First-login caveat (`auth.py:88-100`):** if `cadmin` is still seeded with `reset_password=True`, `POST /auth` returns a **password-reset** token (`action=reset_password`). `jq -r '.access_token'` still extracts it and `POST /event` *accepts* it (`verify_token` rejects only `API`/`SSE_TICKET` contexts), **but it expires in 5 minutes** (`auth.py:30`) — so the automation starts returning 401s minutes after start-up. Complete cadmin's password-reset first-login, or mint from an already-activated user, so the secret is a 24-hour session token.

**Identity to match the JWT** — `MILL_AUTO_USER_KEY` / `MILL_AUTO_CREATED_BY` must be the **User document's `_key`** (the JWT `consumer_key`, `auth.py:92,104`), **not** the login username. The committed `.env` shows the seeded demo value:

```dotenv
MILL_AUTO_USER_KEY=670
MILL_AUTO_CREATED_BY=User/670
```

(`cadmin` is only the username for the mint POST.) These are env-only settings, so a change needs `up -d --force-recreate mill_automation`.

---

## Run it — local (docker compose)

The `config` and `reports` volumes are declared `external: True` (`base.yaml:10-11`, `reporting.yaml`), so compose will **not** create them and the `subpath` mounts fail/mount-empty until they exist. Back each with a **host-bound named volume** — no ad-hoc copy step, and `config` lives at the same `/opt/progress/config` path the server uses, so the live-edit workflow is identical local and server. One-time setup:

```bash
# config → /opt/progress/config (your working copies — edit these directly).
# Seed once from the repo templates, then set the real keys/secrets in place.
sudo mkdir -p /opt/progress/config
sudo cp deploy/config/twinConfig.js deploy/config/mill_automation.json /opt/progress/config/
docker volume create --driver local \
  --opt type=none --opt o=bind --opt device=/opt/progress/config config

# reports → bound straight to the repo's report sources (nothing to copy).
docker volume create --driver local \
  --opt type=none --opt o=bind --opt device="$PWD/demos/reports" reports
```

> macOS/Docker Desktop: add `/opt/progress/config` (and the repo path) under Settings → Resources → File sharing if the bind is refused.
>
> After this, edit `/opt/progress/config/mill_automation.json` and it takes effect on the **next Issue fire — no restart**; edit `/opt/progress/config/twinConfig.js` then `docker compose … up -d --force-recreate demo_twin` (the panel reloads the new config). If the `config` volume is left empty, `demo_twin` falls back to its baked `static/config.js` and `mill_automation` falls back to the `.env` keys.

**Bring the stack up** (run from repo root):

```bash
docker compose \
  -f deploy/compose/base.yaml \
  -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml \
  -f deploy/compose/mill-twin.yaml \
  -p progress-local \
  up -d
```

> `-p progress-local` avoids a project-name collision with a main-repo stack that uses `-p progress`. Stop the main-repo stack first, or use `-p progress-local` here consistently.

**Restart the broker** (local only — required after any `nats-server.conf` edit; the WS config is not hot-reloaded, and locally the conf is a bind mount, `dev.yaml:87`):

```bash
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml \
  -p progress-local restart broker
```

**Smoke checks:**

```bash
# All services (router, api, db, broker, demo_twin, mill_automation, reporting) should be "running"
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml -p progress-local ps

# NATS WebSocket listener active — must return an object with "port": 8090
curl -s http://localhost:8222/varz | jq '.websocket'

# demo_twin reachable directly (local only — :8001 is published by dev.yaml)
curl -s http://localhost:8001/ | head -5

# panel reachable via Traefik route
curl -sI http://progress.localhost/twin | head -5
```

Expected `jq '.websocket'`:

```json
{ "host": "", "port": 8090, "no_tls": true, "...": "..." }
```

A `null` result means the broker has not picked up the WebSocket config — restart it (above). Anonymous WebSocket connections are mapped to a restricted sub-only `ws_browser` identity (`websocket.no_auth_user` in `nats-server.conf:39`) — the panel sends no credentials.

---

## Deployed demo server (Swarm / HTTPS)

The customer-facing server (`demo.progresslab.it`) runs the same images under **Docker Swarm**. Preconditions that differ from local — the base Ansible provisioning (`single_node_setup.yaml`) seeds only `appConfig.js` + `api.env`, so the rest is manual:

1. **Place the demo config files** in `/opt/progress/config/` on the manager node: `twinConfig.js` and `mill_automation.json` (provisioning does not copy them).
2. **Place `nats-server.conf`** (with the `websocket { port: 8090 … }` block) where the broker reads it — `base.yaml`/`stack.yaml` do **not** mount it on Swarm (only local `dev.yaml` does), yet the broker is started with `command: ["-c", "/etc/nats/nats-server.conf"]`. Without it delivered, the broker **crash-loops at startup** (config not found — no 4222 *or* 8090 listener) and `wss://<host>/nats` 502s. Deliver it via a `docker config` or a host bind on the broker service.
3. **Mint the JWT on the manager node** — the `mill_automation_jwt` secret is a file-based compose secret (not `external`), so `${PROGRESS_SECRETS_DIR}/mill-automation.token` must exist on the node performing the deploy.
4. **Set `PROTOCOL`** for the reporting service. `02_MillTwin.py` builds the iframe URL as `${PROTOCOL:-http}://${HOST}/twin/`, and `reporting.yaml` passes only `HOST`. On an HTTPS server an unset `PROTOCOL` yields an `http://` iframe → **mixed-content blocked**. Export `PROTOCOL=https` (it is already in the deploy command below) and ensure the reporting service receives it. *(This is a known gap — see "Open code issues".)*

Deploy (worktree variant — includes the standalone `nats-ws.yaml`; on `DEV` that route is folded into `stack.yaml` and `nats-ws.yaml` is dropped):

```bash
VERSION=0.10.6 HOST=demo.progresslab.it PROTOCOL=https docker stack deploy --resolve-image=never \
  -c base.yaml \
  -c stack.yaml \
  -c tls.yaml \
  -c reporting.yaml \
  -c mill-twin.yaml \
  -c mill-twin-tls.yaml \
  -c nats-ws.yaml \
  progress
```

**Swarm day-2 ops** (no `docker compose restart` under Swarm):

- Apply a `twinConfig.js` edit: `docker service update --force progress_demo_twin` (the bind mount re-points; no image rebuild).
- A `mill_automation.json` edit needs **nothing** — it is re-read on every fire.
- After a `nats-server.conf` edit: if delivered as a **host bind**, `docker service update --force progress_broker`. If delivered as a `**docker config`** (immutable), create a new config object and `docker service update --config-rm <old> --config-add <new> progress_broker`.

---

## The demo beats

Open the Progress webapp (`http://progress.localhost` local, or `https://demo.progresslab.it`).

### Canonical beat (DEMO-01)

1. Navigate to **Reports** in the left sidebar.
2. Click **"MillTwin"** in the report list (the Streamlit page is `02_MillTwin.py`; the nav label is derived from the filename). The panel loads in the report iframe.
3. Confirm the **NATS connect chip** in the panel turns GREEN (no auth prompt). The browser sends no credentials — NATS auto-maps the anonymous WebSocket connection to the sub-only `ws_browser` identity. A green chip proves that mapping (and the WS listener on 8090) works.
4. **Drive torque past the limit.** Drag **Tool Wear** to ~100%, then raise **Feed/tooth** toward its max until the spindle-torque trace crosses the **45 N·m** red dashed line. *(Wear alone tops out at ~39 N·m — torque scales with `depth × feed/tooth × (1 + 0.5·wear)`, so a second lever is required. Depth is already at its slider max, so feed/tooth is the lever to add.)*
5. Hold above the limit for **~5 seconds** (the dwell window).
6. A **"Spindle torque overload: <N.N> N·m"** Issue fires automatically (`detectors.py:92`).
7. Switch to the Progress **Issues view** (left sidebar → Issues).
8. Confirm the Issue exists and is linked to the configured serial / work-order / operation (the keys set in `mill_automation.json`).

This is DEMO-01 end-to-end: the Issue is created in the real Progress database, with full traceability links, purely by driving the panel sliders.

### Backup beat (instant — no dwell)

Press the **Snap-Tool** button → torque collapses to the air-cut floor (~2 N·m, below the 5 N·m breakage floor) and a **"Tool breakage: spindle torque collapsed to <N.N> N·m while feeding"** Issue fires immediately, no dwell (`detectors.py:139-142`). Use this if the torque-dwell path misbehaves. Equivalent call:

```bash
curl -X POST http://progress.localhost/twin/fault \
  -H 'Content-Type: application/json' -d '{"fault":"snap_tool"}'
```

The **Hard Spot** button (`POST /twin/fault {"fault":"hard_spot"}`) injects a ~2 s transient spike to ~96 N·m that auto-decays — a brief spike, not a sustained overload, so on its own it does **not** satisfy the 5 s dwell.

---

## Reset between rehearsals

The physics engine re-seeds to nominal when `demo_twin` restarts (`main.py:82`), or via the panel **Reset** button / `POST /reset`:

```bash
# local
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml \
  -p progress-local restart demo_twin
# server
docker service update --force progress_demo_twin

# either: reset state in place without a restart
curl -X POST http://progress.localhost/twin/reset
```

A fresh Issue is created per rehearsal — scripted Issue cleanup is out of scope; the Issues view accumulates one Issue per run. This is acceptable.

---

## Kill switches

### Disable automation only (keep panel running)

Set `MILL_AUTO_ENABLED=false` (`config.py:84`; `main.py:37-39` exits cleanly), then recreate:

```bash
# local: edit deploy/compose/.env, then
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml \
  -p progress-local up -d --force-recreate mill_automation
# server
docker service rm progress_mill_automation     # or scale to 0 / redeploy with the env set
```

### Stop the panel only

```bash
# local
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml \
  -p progress-local stop demo_twin
# server
docker service rm progress_demo_twin
```

Or use the Docker Desktop UI to stop the container.

### Tear down the whole local stack

```bash
docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml \
  -f deploy/compose/reporting.yaml -f deploy/compose/mill-twin.yaml \
  -p progress-local down
```

`down` (without `-v`) preserves the `external` volumes and the secret source file.

---

## Troubleshooting


| Symptom                                                                                  | Likely cause                                                                                                                  | Fix                                                                                                                                                                                                 |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **No Issue fires**; `mill_automation` log shows `issue fire skipped … no issue_type_key` | `issue_type_key` blank in **both** `mill_automation.json` and `MILL_AUTO_ISSUE_TYPE_KEY` (no 422 — it skips)                  | Set `issue_type_key` in `mill_automation.json` (live, no restart), or `MILL_AUTO_ISSUE_TYPE_KEY` in `.env` then `up -d --force-recreate mill_automation`                                            |
| Issue fires but **links to the wrong / nonexistent records**                             | The non-empty `serial`/`work_order`/`operation` in `mill_automation.json` **override** the `.env` `MILL_AUTO_LINKED_*` values | Put the real seeded `_key`s in `mill_automation.json` (or blank them to use `.env`). *(`twinConfig.js` `WO_LINKS` is display-only — it doesn't affect the link.)*                                                                        |
| Torque **won't cross 45 N·m** with Tool Wear maxed                                       | Wear alone tops out ~39 N·m                                                                                                   | Also raise **Feed/tooth** (depth is already at slider max)                                                                                                                                          |
| Panel loads but live config/WO-links wrong **locally**                                   | `config` volume missing or not bound to `/opt/progress/config`                                                                | Create the host-bound `config` volume (see "Run it — local") and put the files in `/opt/progress/config/`; recreate `demo_twin`                                                                     |
| **"MillTwin" report missing** from the Reports list (local)                              | `reports` volume missing or not bound to the report sources                                                                   | Create the host-bound `reports` volume pointing at `demos/reports`; recreate the reporting service                                                                                         |
| Panel NATS chip stays **red** (local)                                                    | Broker not restarted after `nats-server.conf` edit, or `8090` not published                                                   | `restart broker`; verify `curl -s http://localhost:8222/varz | jq '.websocket'` returns port 8090, and `dev.yaml` broker ports include `8090:8090`                                                  |
| Panel NATS chip stays **red** on the **HTTPS server** (mixed content / 404 on `/nats`)   | `wss://<host>/nats` route missing, broker `8090` listener not running, or `ws://` from an https page                          | Confirm `nats-ws.yaml` is in the deploy and `nats-server.conf` (with `websocket{port:8090}`) reaches the broker; restart broker via `docker service update --force progress_broker`                 |
| Embedded panel **blank on the server**                                                   | reporting service has no `PROTOCOL` → `http://` iframe blocked as mixed content                                               | Ensure `PROTOCOL=https` reaches the reporting service (see "Deployed demo server" step 4)                                                                                                           |
| `POST /twin/setpoints` returns **404**                                                   | `strip-twin-prefix` middleware missing from Traefik labels                                                                    | Verify `strip-twin-prefix.stripprefix.prefixes=/twin` in `mill-twin.yaml`; reapply                                                                                                                  |
| Stack up fails **"secret … does not exist"**                                             | JWT token file not minted before bring-up                                                                                     | Mint it (above); verify `${PROGRESS_SECRETS_DIR}/mill-automation.token` exists                                                                                                                      |
| Issue POST returns **401/403**                                                           | Expired JWT (e.g. a 5-min reset token), empty/missing token file, or token minted against a different `jwt_secret`            | Re-mint a 24-h session token from an activated user; verify the token file is non-empty. *(A `MILL_AUTO_USER_KEY` mismatch does NOT 401 — it silently writes the wrong `created_by` on the Issue.)* |
| Two `api` containers / **port 8000 bind error**                                          | Project-name collision — main stack and worktree stack both running                                                           | Stop the main-repo stack, or use `-p progress-local` consistently                                                                                                                                   |
| `curl http://progress.localhost/twin` returns **502**                                    | `demo_twin` not running or not on the `progress` network                                                                      | `ps`; restart `demo_twin`                                                                                                                                                                           |


---

## Open code issues (flagged by the code audit — not operator-fixable)

These are real defects the runbook can only work around; worth fixing in code:

- `**mill_automation.json` vs `.env` link keys disagree as committed** — the JSON placeholders win, so the numeric `.env` keys are inert. Reconcile the shipped files.
- `**reporting.yaml` doesn't pass `PROTOCOL`** — the embedded panel is mixed-content-blocked on the HTTPS server unless `PROTOCOL=https` reaches `02_MillTwin.py`.
- `**nats-server.conf` is not mounted on Swarm** by `base.yaml`/`stack.yaml` (only local `dev.yaml`) — the server needs a `docker config`/bind to expose the `8090` WS listener.
- `**single_node_setup.yaml` doesn't seed `twinConfig.js` / `mill_automation.json`** into `/opt/progress/config/` — they must be placed manually before deploy.

