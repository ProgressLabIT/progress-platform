---
title: Operations — Admin & Integrator
description: Health checks, log locations, and diagnostic commands for Progress Platform.
---

# Operations

> If you're operating a running Progress Platform deployment, this page covers
> how to verify the stack is healthy, where to find logs, and how to use
> `progress tap` to inspect live event traffic on the broker.

## Health checks

The platform offers three independent health surfaces. Use them in this order
when triaging an incident.

### API liveness — `/api/hello`

`/api/hello` is the API's public unauthenticated endpoint (`GET /hello` in
`backend/api/main.py`, served under the `PROGRESS_API_ROOT_PATH` prefix). It
returns 200 with a small JSON body whenever the FastAPI worker is accepting
requests.

```bash
curl -sS https://<your-host>/api/hello
```

Expected response: HTTP 200 with a short JSON greeting. A non-200 response or
connection refusal indicates the API container is down or Traefik is not
routing `/api`. If a dedicated `/api/health` endpoint is present in your
deployed version, prefer it over `/api/hello` — try `GET /api/health` first
and fall back to `/api/hello` on 404.

### Broker liveness — `/api/broker/health` and `/healthz`

The broker exposes its native monitoring endpoint at
`http://broker:8222/healthz` (declared in `deploy/compose/base.yaml` as the
broker's healthcheck command):

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget -qO- http://127.0.0.1:8222/healthz || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

From outside the swarm, query the broker via the API proxy at
`/api/broker/health` (described in [Integration](/admins/integration)) — it
reports connection status, RTT, and JetStream / MQTT enablement.

### Compose-level service health

Each service that defines a `healthcheck:` block reports `healthy` /
`unhealthy` to Docker. Inspect the rolled-up status:

```bash
# Docker Swarm deployments
docker service ls
docker service ps progress_api --no-trunc

# Standalone Compose
docker compose -f deploy/compose/base.yaml ps
```

The Sparkplug bridge stack (`sparkplug_bridge`, `historian_ingester`,
`sparkplug_sim` in `deploy/compose/sparkplug.yaml`) uses broker-subscription
healthchecks: each service must publish a heartbeat on
`progress.notification.health.sparkplug.<service>` within the timeout window
or Docker marks it unhealthy.

## Log locations

Logs are captured by the Docker engine's default `json-file` driver — there
is no shared `logs:` named volume in `base.yaml`. View logs per service:

- **API container logs** — `docker service logs -f progress_api` (Swarm) or
  `docker compose logs -f api` (standalone). The API uses Gunicorn with
  `--access-logfile -` so HTTP access lines and Python `logging` output share
  the stream.
- **ArangoDB logs** — `docker service logs -f progress_db`. ArangoDB also
  writes durable logs inside the `db_data` volume at `/var/lib/arangodb3`.
- **Broker logs** — `docker service logs -f progress_broker`. Connection
  events, JetStream operations, and slow-consumer warnings appear here.
- **Sparkplug bridge logs** — `docker service logs -f progress_sparkplug_bridge`
  (when the Sparkplug stack is enabled). Includes MQTT connection state,
  bdSeq tracking, and decode errors.
- **Traefik access log** — `docker service logs -f progress_router`. Traefik
  is configured with `--accesslog` so every routed request is logged.

For long-term retention, configure your Docker engine with a logging driver
that ships to your aggregation backend (`syslog`, `journald`, `gelf`,
`fluentd`, or a cloud-vendor driver) on the host or per-service.

## progress tap

`progress tap` streams live event traffic from the Progress Platform NATS
broker to the terminal — it is the primary diagnostic for "did my action
emit the event I expected?".

```bash
# Tail every domain notification with full payloads as JSON
progress tap --format json

# Filter to one subtopic (e.g., production transitions only)
progress tap --subject 'progress.notification.production'

# Tail Sparkplug metric data for a single edge
progress tap --subject 'progress.sparkplug.plant1.edge1.>'
```

Full usage and flag reference: [progress tap](/cli/tap).

When debugging a regression, run `progress tap` on the broker host and trigger
the operator action in the webapp; the matching `progress.notification.*`
line proves the API committed the transaction and published the event.

## Related

- [progress tap](/cli/tap) — full CLI reference
- [Deployment](/admins/deployment) — Compose stack and service names
- [Configuration](/admins/configuration) — environment variables read at runtime
- [Integration](/admins/integration) — `/api/broker/health` and bridge health
