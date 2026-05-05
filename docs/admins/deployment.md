---
title: Deployment — Admin & Integrator
description: Docker Compose stack overview for Progress Platform deployment.
---

# Deployment

> If you're deploying Progress Platform, this page covers the Docker Compose stack
> layout, the named volumes the stack mounts, the Docker secrets the API and
> database read at startup, and how Traefik routes external traffic to the API
> and webapps. Every name here is extracted verbatim from the files under
> `deploy/compose/`.

## Compose files

A typical production deployment combines `stack.yaml` (Swarm placement, secrets,
Traefik routing) on top of `base.yaml` (service definitions, volumes). Optional
extension files layer additional capabilities. The `progress init` CLI generates
the matching combination — see [progress init](/cli/init).

| File | Role |
|------|------|
| `deploy/compose/base.yaml` | Production base — defines `router`, `api`, `db`, `broker`, the named volumes (`media`, `db_data`, `db_backup`, `nats_data`), and the broker NATS healthcheck. |
| `deploy/compose/stack.yaml` | Docker Swarm overlay — adds external `progress` network, Docker secrets, Traefik labels and routers, and the `app` (main webapp) service. |
| `deploy/compose/dev.yaml` | Local-development overrides for the base stack. |
| `deploy/compose/sparkplug.yaml` | Optional Sparkplug bridge extension (`sparkplug_bridge`, `historian_ingester`, `sparkplug_sim`). |
| `deploy/compose/warehouse.yaml` | Optional warehouse SPA service. |
| `deploy/compose/workflow.yaml` | Prefect workflow engine + workflow database. |
| `deploy/compose/tls.yaml` | Traefik TLS overrides for HTTPS-terminating deployments. |
| `deploy/compose/integration.yaml` | Integration / printing / reporting overlays. |

## Services

Service names and image tags are taken directly from `base.yaml` and `stack.yaml`.

| Service | Image | Purpose |
|---------|-------|---------|
| `router` | `traefik:v2.11` | Reverse proxy. Listens on host ports 80, 443, and 8080 (dashboard). Reads Docker labels for routing. |
| `db` | `arangodb:3.11` | ArangoDB multi-model database. Reads root password from `progress_db_root_pwd` Docker secret. |
| `api` | `registry.gitlab.com/progresslab/progress-platform/api:${VERSION}` | FastAPI backend. Reads `PROGRESS_API_DB_PWD`, `PROGRESS_JWT_SECRET`, `PROGRESS_ADMIN_PWD` from Docker secrets. |
| `app` | `registry.gitlab.com/progresslab/progress-platform/app:${VERSION}` | Main webapp (Quasar SPA). Mounts `appConfig.js` and the `media` volume read-only. |
| `broker` | `nats:2.12-alpine` | NATS message broker. Exposes 4222 (NATS), 8222 (HTTP monitoring), 1883 (MQTT). Native `/healthz` healthcheck. |
| `warehouse` (optional) | `registry.gitlab.com/progresslab/progress-platform/warehouse:${VERSION}` | Warehouse SPA. Activated via `deploy/compose/warehouse.yaml`. Routed under `/wh` prefix. |
| `sparkplug_bridge` (optional) | `registry.gitlab.com/progresslab/progress-platform/sparkplug-bridge:${VERSION}` | Decodes Sparkplug B MQTT frames and re-emits them on NATS. Activated via `sparkplug.yaml`. |

The Sparkplug optional services (`sparkplug_bridge`, `historian_ingester`, `sparkplug_sim`)
are described in [Integration](/admins/integration).

## Named volumes

All volumes in `base.yaml` are declared `external: true` — create them once before the
first `docker stack deploy`.

- **`media`** — uploaded attachments (mounted at `/media` in the `api` container, the
  `PROGRESS_MEDIA_PATH` target). Also mounted read-only into `app` so the webapp can
  serve attachment images directly.
- **`db_data`** — ArangoDB on-disk data files (`/var/lib/arangodb3` in the `db` container).
- **`db_backup`** — ArangoDB backup target (`/db_backup` in the `db` container). Used by
  `progress restore` and scheduled `arangodump` jobs.
- **`nats_data`** — NATS broker JetStream KV state (`/data` in the `broker` container).
  Holds `sparkplug_sessions`, `sparkplug_aliases`, `sparkplug_last_seq`, and
  `sparkplug_last_values` buckets when the Sparkplug bridge is enabled.

Create with:

```bash
docker volume create media
docker volume create db_data
docker volume create db_backup
docker volume create nats_data
```

## Docker secrets

`stack.yaml` declares four external secrets. They MUST exist in the swarm before
`docker stack deploy progress` runs, otherwise the `api` and `db` services fail to
start with "secret not found".

| Secret name | Purpose | How to create |
|-------------|---------|---------------|
| `progress_db_root_pwd` | ArangoDB root password (read by `db` via `ARANGO_ROOT_PASSWORD_FILE=/run/secrets/progress_db_root_pwd`). | `echo "<value>" \| docker secret create progress_db_root_pwd -` |
| `progress_api_db_pwd` | Password for the `progress_api` ArangoDB user that the FastAPI backend connects with. | `echo "<value>" \| docker secret create progress_api_db_pwd -` |
| `progress_jwt_secret` | HMAC secret used by the API to sign and verify JWT bearer tokens. | `echo "<value>" \| docker secret create progress_jwt_secret -` |
| `progress_admin_pwd` | Bootstrap password for the seed admin user created on first DB initialization. | `echo "<value>" \| docker secret create progress_admin_pwd -` |

Secrets are mounted by Docker at `/run/secrets/<name>` inside the `api` container; the
backend reads the file contents at startup. The values are never written to logs or
to the configuration table.

## Traefik routing

Traefik is configured in `stack.yaml` with three command-line flags worth knowing:

- `--providers.docker.swarmMode` — Traefik watches Docker swarm services (not standalone
  containers) and reads routing rules from each service's `deploy.labels`.
- `--providers.docker.exposedbydefault=false` — services are NOT routed unless they
  explicitly set `traefik.enable=true`.
- `--entrypoints.web.address=:80` — Traefik listens on port 80 inside the network; the
  `router` service publishes 80 → 80 to the host.

Routing rules from the `traefik.http.routers.*` labels:

| Path | Service | Notes |
|------|---------|-------|
| `/api` | `api` | `stripprefix` middleware removes `/api` before forwarding. The API also reads `PROGRESS_API_ROOT_PATH=/api` so its own OpenAPI / docs URLs include the prefix. Priority 10. |
| `/_db` | `db` | ArangoDB web UI, with a `replacepathregex` middleware that rewrites `/_db` to `/`. Priority 10. |
| `/` | `app` | Catch-all for the main webapp. Priority 1, so `/api` and `/_db` win. |
| `/wh` (optional) | `warehouse` | Warehouse SPA, `stripprefix` removes `/wh`. Defined in `warehouse.yaml`. |

The host the rules match is `Host(\`${HOST}\`)` — set `HOST` in your environment file
before deploying. The Traefik dashboard is available on port 8080 when
`--api.insecure` is set (default in `stack.yaml`); restrict that port at the firewall
layer in production.

## Related

- [progress init](/cli/init) — provisions the Compose stack from a template
- [Configuration](/admins/configuration) — every `PROGRESS_*` environment variable
- [Integration](/admins/integration) — Sparkplug bridge stack and HTTP read API
- [Operations](/admins/operations) — health checks and diagnostic commands
