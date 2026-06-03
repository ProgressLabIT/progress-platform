# 0006 — `progress init` Typer CLI UX (Docker Swarm port of `single_node_setup.yaml`)

**Status:** decided
**Date:** 2026-04-28
**Revised:** 2026-04-28 (rebased on the actual `deploy/single_node_setup.yaml` Ansible playbook; switched from compose-up to swarm-stack-deploy; dropped the channel concept; dropped the "Next:" hint)
**Audience:** S4 (CLI session), S5 (demo data + walkthrough), demo presenter
**Supersedes:** none

## Context

The demo opens with a fresh Linode Ubuntu LTS VM that the presenter
provisions live on a webinar with 5–10 viewers. The first segment runs
`progress init` to bring up the Progress stack so the audience sees a
believable bootstrap from nothing.

Progress's existing single-node deployment lives in
`deploy/single_node_setup.yaml`, an Ansible playbook that installs
Docker, sets up `/opt/progress/`, creates volumes and overlay networks,
generates secrets, deploys the stack on **Docker Swarm**, and runs an
init-db service. The original draft of this ADR mistakenly assumed
Progress used `docker compose`; in fact it uses `docker swarm` +
`docker stack deploy`. This revision rebases the CLI shape on the actual
Ansible playbook so `progress init` is a faithful Python+Typer port of
that procedure.

The user has confirmed:

- Typer for the CLI.
- Both interactive prompts and declarative flags supported, with the
  interactive path used on stage.
- The interactive UX is the demo's selling point ("look how easy"), so the
  prompts must be tight, narrate well, and not surface ops noise the
  audience doesn't care about.
- Drop the "Next:" hint section that appeared in the previous draft.
- Use a `--release` flag to specify the GitLab registry tag (e.g.
  `v0.10.0`), matching the playbook's `VERSION` env var.

## Decision

### Command shape

`progress init` is a Typer subcommand registered in `cli/main.py`. It is
invoked as root (or via `sudo`) on a freshly provisioned host.

```
Usage: progress init [OPTIONS]

Options:
  --release TEXT             Release tag to deploy from the registry
                             (e.g. v0.10.0). Maps to the playbook's
                             VERSION env var. Default: latest pinned
                             tag bundled with the CLI.
  --host TEXT                Public hostname for the Progress UI.
                             Maps to the playbook's HOST env var.
                             Skipped in --no-tls mode where the host's
                             IP is used.
  --enable-tls / --no-tls    Provision a Let's Encrypt certificate via
                             Traefik's ACME resolver (requires --host
                             with DNS pointing here). Default for the
                             demo: --no-tls.
  --tls-email TEXT           Email for Let's Encrypt notifications.
                             Required when --enable-tls is set.
  --admin-email TEXT         Email of the initial admin user.
  --admin-password TEXT      Initial admin password. If omitted, generated
                             and printed once.
  --registry-username TEXT   GitLab registry username for image pulls.
                             Default: bundled deploy-time creds.
  --registry-token TEXT      GitLab registry token. Default: bundled.
  --skip-pull                Don't pre-pull images; useful when re-running.
  --non-interactive          Refuse all prompts; require flags for everything.
  --help                     Show this and exit.
```

When invoked with no flags, the command runs the interactive flow below.

### Interactive flow

The presenter's terminal shows a sequence of prompts, each preceded by a
short context line. The flow is intentionally short — six questions max —
so the audience can read the bootstrap as it happens.

```
$ progress init

Progress Platform installer.

  Where will the UI be reached?
  Enter a domain name (with DNS pointing here) or press Enter to use this
  host's IP for HTTP-only mode (recommended for demos).

  Domain [press Enter for HTTP]: ░

  Enable TLS via Let's Encrypt? Requires the domain above to resolve to
  this host.

  Enable TLS? [y/N]: ░

  TLS notification email: ░          (only asked when TLS is enabled)

  Initial admin user.

  Email: ░

  Password (Enter to generate one): ░

  Release to deploy.

  Tag (default: v0.10.0): ░

  Ready to install. This will:

    - create /opt/progress with the Progress directory layout
    - install Docker if not present
    - log in to the GitLab container registry
    - create Docker volumes and the progress + reporting overlay networks
    - initialize Docker Swarm
    - generate Docker secrets (DB and JWT credentials)
    - pull image set (~600 MB)
    - deploy the Progress stack
    - run the database init service to bootstrap users
    - create the initial admin user

  Proceed? [Y/n]: ░
```

After confirmation, the command runs the install steps with progress
output. Each step is a single line with a status indicator the audience
can follow in real time:

```
  ▸ Checking prerequisites          ✓
  ▸ Installing Docker               ✓ (already installed)
  ▸ Creating /opt/progress          ✓
  ▸ Creating directory layout       ✓ (15 subdirectories)
  ▸ Logging in to registry          ✓
  ▸ Creating Docker volumes         ✓ (11 volumes)
  ▸ Initializing Docker Swarm       ✓
  ▸ Creating overlay networks       ✓ (progress, reporting)
  ▸ Generating Docker secrets       ✓ (4 secrets)
  ▸ Pulling images for v0.10.0      ✓ (47s)
  ▸ Rendering progress.env          ✓
  ▸ Deploying stack                 ✓
  ▸ Running database init           ✓ (12s)
  ▸ Waiting for API to be ready     ✓
  ▸ Creating admin user             ✓

  Progress is up at:    http://203.0.113.42

  Login as:             admin@example.com
  Generated password:   M7q-x42-pP8g
```

(The "Next:" hint section that appeared in the previous draft is
deliberately omitted; it pollutes a real-world install transcript.)

### Behaviour and side effects

`progress init` ports the Ansible playbook in `deploy/single_node_setup.yaml`
to Python. Each step is idempotent; rerunning the command after a partial
failure resumes from the first incomplete step.

1. **Prerequisite check.** Confirms the host is Linux (Ubuntu Noble or
   compatible), has 4+ GB RAM, has 20+ GB free disk on `/`, and reaches
   Docker Hub and the GitLab registry.

2. **System packages.** Installs `aptitude`, then `apt-transport-https`,
   `ca-certificates`, `curl`, `software-properties-common`, `python3-pip`,
   `python3-venv`, `python3-setuptools`. Mirrors the playbook's apt block.

3. **Docker install.** Adds the Docker GPG key and apt repository, installs
   `docker-ce`. If Docker is already present at version ≥ 24, skips. Older
   Docker triggers a hard error.

4. **Layout creation.** Creates `/opt/progress/` with the Ansible playbook's
   exact directory list:

   ```
   /opt/progress/
     db_data/
     db_backup/
     workflow_db/
     workflow_config/
     flows/
     media/
     logs/
     reports/
     cmounts/
     notebooks/
     letsencrypt/
       custom/         (mode 0700)
     config/
   ```

5. **Compose / stack file deployment.** Writes the stack files into
   `/opt/progress/config/` from the CLI's bundled copy. Files include
   `base.yaml`, `stack.yaml`, `tls.yaml`, `warehouse.yaml`,
   `workflow.yaml`, `integration.yaml`, `reporting.yaml`, `notebooks.yaml`,
   plus the new `sparkplug.yaml` for the demo. CLI ships these in its
   package data; no network fetch.

6. **API config.** Copies `appConfig.js` and `api.env` into
   `/opt/progress/config/`, mirroring the playbook's copy block.

7. **Reports app files.** Copies `main.py` and `entrypoint.sh` into
   `/opt/progress/reports/`.

8. **Render `progress.env`.** Writes `/opt/progress/config/progress.env`
   from the CLI's template, populated with the user's answers
   (`VERSION`, `HOST`, `ENABLE_TLS`, `TLS_EMAIL`).

9. **Registry login.** Runs `docker login` against
   `registry.gitlab.com/progresslab/progress-platform` using the bundled
   or flag-provided credentials.

10. **Docker volumes.** Creates the eleven external Docker volumes the
    compose files declare, each as a bind mount under `/opt/progress/<vol>`:
    `db_data, db_backup, workflow_db, workflow_config, flows, media,
    logs, reports, cmounts, notebooks, letsencrypt`. Plus the
    `historian_data` volume is NOT created — historian lives in
    `workflow_db` per ADR-0005's consolidation.

11. **Swarm init.** Runs `docker swarm init` on the local host. Captures
    the join tokens for forensics; v1 demo is single-node so no workers
    join.

12. **Overlay networks.** Creates `progress` and `reporting` overlay
    networks attachable.

13. **Docker secrets.** Generates random secrets via `openssl rand -hex
    <length>` and pipes to `docker secret create`. The secret list mirrors
    the Ansible playbook plus the new ones for this demo:

    | Secret name | Length (hex) | Purpose |
    |---|---|---|
    | `progress_api_db_pwd` | 32 | API ↔ ArangoDB |
    | `progress_admin_pwd` | 16 | Initial admin user |
    | `progress_jwt_secret` | 32 | JWT signing |
    | `progress_db_root_pwd` | 16 | ArangoDB root |
    | `progress_workflow_db_pwd` | 16 | Postgres / Prefect role (NEW per ADR-0005) |
    | `progress_historian_db_pwd` | 16 | Postgres / historian role (NEW per ADR-0005) |
    | `progress_sparkplug_token` | 32 | Sparkplug bridge service-user JWT seed (NEW; the actual JWT is issued post-init) |

14. **Image pull.** `docker compose --env-file progress.env pull` against
    the assembled stack files unless `--skip-pull` is set.

15. **Stack deploy.** Runs `docker stack deploy --with-registry-auth -c base.yaml -c stack.yaml [-c tls.yaml] -c warehouse.yaml -c workflow.yaml -c integration.yaml -c reporting.yaml -c notebooks.yaml progress`. The `tls.yaml` overlay is included only when `ENABLE_TLS` is `true`.

16. **DB init service.** Runs the same `init-db` Docker service the
    playbook runs: image `<registry>/api`, command `python3 /db_init.py`,
    bind-mounts `/opt/progress/db_init.py` and `/opt/progress/config`,
    secrets attached. Blocks until the service exits successfully.

17. **Readiness wait.** Polls the API health endpoint for up to 120 s.

18. **Admin user creation.** Calls the API to create the initial admin
    using either the provided or generated password.

19. **Marker.** Writes `/opt/progress/config/.progress-installed` with the
    release tag and ISO timestamp; a re-run of `progress init` refuses to
    proceed unless this file is removed or `--upgrade` is used (the upgrade
    path is post-demo work).

20. **Summary.** Prints the summary block shown above.

The demo flow runs `progress restore <archive>` and
`docker stack deploy -c sparkplug.yaml progress` separately AFTER
`progress init` completes, so init's path is identical to a real-world
install.

### Flag-only / non-interactive mode

`progress init --non-interactive --host progress.example.com --no-tls --admin-email admin@example.com --release v0.10.0 --skip-pull`

is equivalent to the interactive path with those answers and bypasses all
prompts. Used for CI tests and unattended re-runs.

### What is NOT in v1

- No SaaS / cloud bootstrap path. Linux host (Ubuntu LTS) only.
- No multi-tenant install (single-tenant matches Progress's shipping model).
- No upgrade path. `progress init` refuses to run on a host where the
  marker file already exists; the user must remove it explicitly.
- No `systemd` unit. Docker Swarm + the platform's restart policies handle
  service lifecycle. The marker file records install completion.
- No DNS provisioning or domain registration; `--host` is informational.

### Demo presentation notes

For the May 15 webinar:

- `--no-tls` is the default demo path; `--enable-tls` is rehearsed but
  used only if the second rehearsal proves it works reliably (LE failure
  on stage is unrecoverable).
- Set `--admin-email` via answer at the prompt's preamble narration so the
  audience sees a meaningful email rather than the presenter's personal
  one.
- The image-pull phase is the load-bearing minutes of the segment. The
  presenter narrates Progress architecture during the pulls.
- A pre-snapshotted Linode image with Docker already installed cuts ~30 s;
  the install banner still shows "Docker found, skipping." which is honest.
  Decide rehearsal-time whether to use the snapshot or a fully fresh image.

### Failure modes

Each install step has a labelled failure path that prints actionable next
steps. The presenter has a written fallback for each one. The most likely
failure modes in priority order:

1. Docker Hub rate limit. Mitigation: pre-authenticate the Linode with a
   Docker Hub account during the rehearsal.
2. Image pull timeout. Mitigation: re-run; `--skip-pull` if pulls are
   already done.
3. Stack deploy failure (Swarm not initialized, network exists, etc.).
   Mitigation: idempotent re-run; `docker stack rm progress` + retry as a
   reset.
4. Admin user creation fails. Mitigation: presenter has a one-liner to
   create admin manually using the JWT secret.
5. LE provisioning failure (only when `--enable-tls`). Mitigation: re-run
   with `--no-tls`.

A `progress init --resume` flag is deliberately NOT added; the command is
already idempotent and resuming is "run it again."

## Trade-offs and rejected options

**Compose-up vs Swarm + stack-deploy.** The original draft assumed `docker
compose up`; the actual playbook uses `docker swarm init` + `docker stack
deploy`. Rebased to match the playbook so the CLI is a faithful port and
deployment shape doesn't drift from production. Single-node Swarm has
near-zero overhead vs Compose and gains overlay networks, secrets, and
parity with a future multi-node deployment.

**Channels (`stable`/`edge`) vs `--release` tag.** Original draft used
channels; the playbook uses a literal `VERSION` env var pointing at a
GitLab registry tag. Aligned: `--release v0.10.0` (or any tag pushed to
the registry).

**Show the "Next:" hint at the end.** Removed. It pollutes a transcript
that should look like a real install. The walkthrough script's narration
covers the next steps verbally.

**TLS by default.** Reverted to `--no-tls` as the recommended demo path,
both supported by the CLI; rehearsal decides which the May 15 demo uses.

**Show `docker pull` raw output.** Rejected. The native output is noisy
and inconsistent across image sizes. CLI shows one line per image with a
duration, computed from the underlying call.

**Asking the user to confirm Docker install.** Kept. Auto-installing
Docker without confirmation is hostile on a "fresh Ubuntu" that may not
actually be fresh.

## Consequences

- S4 (CLI session) implements `progress init` per the steps above. The
  CLI ships `cli/init.py`, `cli/restore.py`, `cli/tap.py` plus
  registration in `cli/main.py`. Stack files (base.yaml, stack.yaml,
  tls.yaml, warehouse.yaml, workflow.yaml, integration.yaml,
  reporting.yaml, notebooks.yaml, sparkplug.yaml) are bundled as CLI
  package data.
- S5 (demo data) ensures the restored DB does NOT include an admin user;
  `progress init` is the canonical way to create one. The restored DB
  ships only post-init data: the demo work orders, phases, products, the
  `USR-SPARKPLUG-BRIDGE` user, and the JWT for that user written to
  `/opt/progress/config/.sparkplug-token`.
- The compose / stack files bundled into the CLI package are the same
  files used in `deploy/compose/` for development; `progress init` copies
  them into `/opt/progress/config/` at install time.
- A separate `progress restore` command is what the demo uses next; it
  operates against the running stack and expects `progress init` to have
  completed.

## Related

- `deploy/single_node_setup.yaml` — the Ansible playbook this CLI ports.
- `deploy/single_node_setup_local.yaml` — local-host variant; CLI's behaviour
  is closer to the production-host path.
- `cli/main.py` — Typer app registration.
- `deploy/compose/` — base stack files bundled into the CLI.
- ADR-0001 — demo flow that places `progress init` as segment 1.
- ADR-0005 — Postgres consolidation; affects the secret list and the
  workflow-db image.
