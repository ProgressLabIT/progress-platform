---
title: progress init
description: progress init reference — Progress Platform.
cli_validated: false
---

# `progress init`

> Bootstraps a fresh Linux host into a single-node Progress deployment by porting the `deploy/single_node_setup.yaml` Ansible playbook to a Typer command. Runs as root, installs Docker if missing, creates `/opt/progress/` with the volume layout, generates Docker secrets, initializes Swarm, deploys the stack, runs the database init service, and creates the initial admin user. Idempotent — rerunning resumes from the first incomplete step.

> 🚧 Coming soon — `progress init` is in active development; this page will be promoted to validated content when the underlying source lands.

## When to use it

- When a webinar attendee opens a fresh Linode (or any Ubuntu LTS) VM and follows the README quickstart on stage.
- When a presenter rehearses the demo bootstrap from nothing — `progress init` is segment 1 of the Sparkplug demo flow per ADR-0001.
- When an operator needs to reprovision a single-node host and wants the Ansible-equivalent path without invoking Ansible.
- When CI needs an unattended re-run via `--non-interactive` plus the relevant flags.

## Usage

```bash
progress init [OPTIONS]
```

Run as root (or via `sudo`). With no flags, the command runs the interactive flow (six prompts max). With `--non-interactive`, every answer must be supplied via flags.

## Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--release` | `TEXT` | latest pinned tag bundled with the CLI | Release tag to deploy from the registry (e.g. `v0.10.0`). Maps to the playbook's `VERSION` env var. |
| `--host` | `TEXT` | _(none)_ | Public hostname for the Progress UI. Maps to the playbook's `HOST` env var. Skipped in `--no-tls` mode where the host's IP is used. |
| `--enable-tls` / `--no-tls` | `FLAG` | `--no-tls` | Provision a Let's Encrypt certificate via Traefik's ACME resolver. Requires `--host` with DNS pointing here. `--no-tls` is the recommended demo path. |
| `--tls-email` | `TEXT` | _(none)_ | Email for Let's Encrypt notifications. Required when `--enable-tls` is set. |
| `--admin-email` | `TEXT` | _(none)_ | Email of the initial admin user. |
| `--admin-password` | `TEXT` | generated and printed once | Initial admin password. If omitted, generated and printed once at the end of the run. |
| `--registry-username` | `TEXT` | bundled deploy-time creds | GitLab registry username for image pulls. |
| `--registry-token` | `TEXT` | bundled deploy-time creds | GitLab registry token for image pulls. |
| `--skip-pull` | `FLAG` | _(off)_ | Don't pre-pull images; useful when re-running after a partial failure. |
| `--non-interactive` | `FLAG` | _(off)_ | Refuse all prompts; require flags for every answer. |
| `--help` | `FLAG` | _(off)_ | Show the help text and exit. |

Source: ADR-0006 §"Command shape" (the locked UX). Once `cli/init.py` ships, this table is regenerated from the Typer-decorated function signature and `cli_validated` flips to `true`.

## Example

The non-interactive flow used in CI and unattended re-runs:

```bash
$ sudo progress init \
    --non-interactive \
    --host progress.example.com \
    --no-tls \
    --admin-email admin@example.com \
    --release v0.10.0 \
    --skip-pull

  ▸ Checking prerequisites          ✓
  ▸ Installing Docker               ✓ (already installed)         # idempotent — Docker ≥ 24 is reused
  ▸ Creating /opt/progress          ✓
  ▸ Creating directory layout       ✓ (15 subdirectories)         # ports the playbook's directory list
  ▸ Logging in to registry          ✓
  ▸ Creating Docker volumes         ✓ (11 volumes)                # external bind-mounts under /opt/progress/<vol>
  ▸ Initializing Docker Swarm       ✓
  ▸ Creating overlay networks       ✓ (progress, reporting)
  ▸ Generating Docker secrets       ✓ (4 secrets)                 # openssl-rand into `docker secret create`
  ▸ Pulling images for v0.10.0      ✓ (skipped — --skip-pull)
  ▸ Rendering progress.env          ✓
  ▸ Deploying stack                 ✓                              # docker stack deploy --with-registry-auth
  ▸ Running database init           ✓ (12s)                        # init-db service from the registry's api image
  ▸ Waiting for API to be ready     ✓
  ▸ Creating admin user             ✓

  Progress is up at:    http://progress.example.com

  Login as:             admin@example.com
  Generated password:   M7q-x42-pP8g
```

Transcript shape grounded in ADR-0006 §"Interactive flow"; once `cli/init.py` ships, this example is replaced with a captured live run.

## How it maps to the Compose stack

Each step in the install touches a specific file under `deploy/compose/`, a named Docker volume, or a Docker secret. The CLI ships these compose files as Python package data so the bundled stack is identical to the development tree.

| Step | Compose target | Volume / Secret |
|------|----------------|-----------------|
| Layout creation (`/opt/progress/db_data/`) | `deploy/compose/base.yaml` (`db` service) | volume `db_data` (external) |
| Layout creation (`/opt/progress/db_backup/`) | `deploy/compose/base.yaml` (`db` service) | volume `db_backup` (external) |
| Layout creation (`/opt/progress/media/`) | `deploy/compose/base.yaml` (`api` service) | volume `media` (external) |
| Layout creation (`/opt/progress/logs/`) | `deploy/compose/base.yaml` (host bind) | host directory `logs` |
| Generate Docker secrets | `deploy/compose/stack.yaml` (`secrets:` block) | secret `progress_api_db_pwd` |
| Generate Docker secrets | `deploy/compose/stack.yaml` (`secrets:` block) | secret `progress_admin_pwd` |
| Generate Docker secrets | `deploy/compose/stack.yaml` (`secrets:` block) | secret `progress_jwt_secret` |
| Generate Docker secrets | `deploy/compose/stack.yaml` (`secrets:` block) | secret `progress_db_root_pwd` |
| Broker bring-up | `deploy/compose/base.yaml` (`broker` service) | volume `nats_data` (external) |
| Stack deploy — API | `deploy/compose/stack.yaml` (`api` service) | image `registry.gitlab.com/progresslab/progress-platform/api:${VERSION}` |
| Stack deploy — Traefik routing | `deploy/compose/stack.yaml` (`router` service) | host port `80` (HTTP) |
| Stack deploy — TLS overlay (when `--enable-tls`) | `deploy/compose/tls.yaml` | volume `letsencrypt` |
| Database init service | `deploy/compose/stack.yaml` (`api` image) | secrets `progress_api_db_pwd`, `progress_admin_pwd`, `progress_jwt_secret` |

Volumes and secrets are sourced from `deploy/compose/base.yaml` (`volumes:`) and `deploy/compose/stack.yaml` (`secrets:`). The `--release` flag becomes the `VERSION` env var that resolves the registry image tag in `stack.yaml`.

## Related

- [Deployment basics](/admins/deployment) — what `progress init` provisions
- [Operations](/admins/operations) — `progress tap` as a diagnostic
- [progress restore](/cli/restore) — restore demo or backup data after `init` completes
- [ADR-0006](https://github.com/ProgressLabIT/progress-platform/blob/DEV/km/decisions/0006-progress-init-ux.md) — Source of truth for `progress init` UX
