# Release Notes — 0.10.x

Notes for the published `v0.10.x` tags that did not yet have a GitLab release.
Each section corresponds to a git tag and is intended to be used as the body of
the matching release at
[`progresslab/progress-platform/-/releases`](https://gitlab.com/progresslab/progress-platform/-/releases).

Previous release: **BETA 9.4 (`v0.9.4`)**, 2025-07-04.

---

## BETA 10.0 — `v0.10.0`

Released 2026-04-27. 412 commits since `v0.9.4`. Milestone:
[0.10.0 (iid 11)](https://gitlab.com/progresslab/progress-platform/-/milestones/11).

### New Features

#### Task Management

- Define tasks with code, title and description, and create multiple task types
  each with a dedicated form.
- Link tasks to platform entities — products, serials, work orders, issues and
  other tasks — with link rules configured per task type (which entities may be
  linked, whether a link is mandatory for completion, whether multiple entities
  of the same type are allowed).
- Status lifecycle: `pending → open → completed → canceled`, plus task
  suspension.
- `start_from` and `due_by` scheduling with a "late" indicator.
- Set an **active task** and automatically link events raised across the
  platform to it (e.g. a serial update is linked to the active repair task).
- `TaskOverview` screen with multiselect and bulk/mass status updates.
- `TaskType` configuration screen and dedicated task routes.

#### Inventory Counting

- Stock Counting sessions, blind (no expected quantity)
  and non-blind counting modes, and a position browser.
- Snapshot-based reconciliation (`InventorySnapshot`) and generation of
  adjustment-type movement lists after a count is confirmed.
- Aggregation across count records with serial uniqueness checks within a
  position.

#### Printing v2

- Reworked print-template model and `PrintTemplateDesigner` (blank base
  dimensions, help reference, copyable templates).
- Expanded ZPL output: plain and free-form (non-GS1) datamatrix, multi-line
  single fields, configurable max field lines.
- Print delivered through a dedicated `print_service` user / print service.

#### User Hub and New User Menu

- New quick-panel user menu, `/user` hub and `UserHome` landing screen.
- Configurable homepage (including task root as a homepage option).

#### Custom JSON Data

- `CustomData` collection, Pydantic model with key validation, and full CRUD
  endpoints.
- `CustomDataLibrary` master-detail view and `CustomDataDetail` editor with
  i18n, a value column, copy-as-new and key-validation error messages, wired
  into admin routing and tabs.

#### Counter Management

- System-counter configuration with template validation and preview.
- Deletion guard preventing removal of counters that are in use.

#### Real-time / SSE

- SSE-driven updates for single work order/job records in planning screens.
- SSE issue notifications in `WorkSessionScreen` and a notifications panel in
  the new user menu.

### Breaking Changes

These require deployment or data changes — see **Upgrade Procedure**.

- **HTTP → HTTPS** service routing (new compose files, Let's Encrypt volume,
  `progress.env` version file). Optional but recommended.
- **Prefect 2 → 3** migration — workers replace queues; flows/loaders updated
  for Pydantic 2 and Prefect 3 APIs.
- **Print-template schema v5** — existing templates must be migrated.
- **System counters config shape** — counter attributes now live at the root of
  the `Config/system_counters` record.
- New collections introduced for Task Management and Inventory Counting (see
  below) must exist before the app starts.

### Improvements and Bugfixes

- Cached-webapp staleness after updates prevented (clients no longer serve a
  stale SPA build post-deploy).
- Event-engine robustness: free the cursor before creating child events to avoid
  transaction conflicts; `event_source` added to the spawning transaction;
  fixes to `InventoryChangedEvent`, `SerialReleased`, `ActiveBatchChangedEvent`
  (no `batch_serials`), `JobReset`/`JobResumed` with an active batch, and
  `ProgressOverride`.
- Job/work-order accuracy: correct `next_batch_available` when
  `production_batch` is 0 and after a split; work-order/phase keys recorded on
  job event records; `JobClosed` transaction collections fixed in
  `update_work_order_quantities`.
- Counting fixes: count aggregation at level 0, stale-record filtering, count
  session status updates after processing completes, decimals handling in the
  warehouse app, automatic initial-position selection.
- Pydantic 2 hardening: `@classmethod` added to field validators where missing.
- Numerous UI fixes across counting, tasks, print dialog, autocomplete/prompt
  base components and the warehouse app; broad refactor toward `<script setup>`.
- Deployment fixes: missing config files added; compose env vars usable with
  both a server IP and a domain name; client calls to the Prefect server fixed.

### Upgrade Procedure

> Source: 0.10.0 milestone description. Apply in order on a backed-up instance.

**1. HTTP → HTTPS** (optional, requires service-spec update)

- Create the Let's Encrypt folder and volume.
- Adjust `appConfig.js` if necessary.
- Create a `progress.env` file with version info.
- Update the docker compose files.
- Redeploy the whole stack with the new service routing.

**2. Database**

- Update `Config/system_counters` so counter attributes sit at the **root** of
  the record.
- Add Task collections: `Task`, `task_rel`, `TaskType`, `event_source`.
- Add Inventory Counting collections: `InventoryCountSession`,
  `InventoryCountAssignment`, `inventory_count_record`, `InventorySnapshot`,
  `inventory_snapshot_item`, `inventory_count_position_complete`.
- Ensure a `default` counter exists, e.g.:
  ```json
  {
    "next_tick": 514,
    "template": ["%y", "OP", "#5"],
    "frequency": "year",
    "reset_date": "2025-01-01T00:00:00+01:00",
    "name": "Test"
  }
  ```
- Add `tasks` and `counting_sessions` counters to `Config/system_counters`.
- Add the `separator` record to the `CustomField` collection:
  ```json
  {
    "_key": "separator",
    "type": "separator",
    "name": "-",
    "default_label": null,
    "default_hint": null
  }
  ```

**3. Printing v2**

- Migrate the printers model (add `type` and `timeout`).
- Migrate print templates with `db/migrations/227-print-template-schema-v5.py`.
- Add a `print_service` user and set its password as a docker secret.
- Add a `.env` on the print server with
  `PROGRESS_PRINT_SERVICE_API_PASSWORD` and `PROGRESS_PRINT_SERVICE_API_URL`.
- Deploy the print service.

**4. Prefect 2 → 3**

- Deactivate all deployments; remove the system and integration agent services.
- Back up the workflow DB volume (from `/opt/progress`):
  ```bash
  export POSTGRES=$(docker ps -qf name=workflow-db) NOW=$(date '+%Y%m%d-%H%M%S')
  docker pause $POSTGRES
  docker exec -t $POSTGRES pg_dump -U postgres -d prefect > db_backup/prefect_backup_$NOW.sql
  # restore: cat db_backup/prefect_backup_$NOW.sql | docker exec -i $POSTGRES psql -U postgres -d prefect
  ```
- Update startup scripts (`Dockerfile`, `entrypoint.sh`, compose spec) to use
  **workers** instead of queues.
- Resume Postgres: `docker unpause $POSTGRES`.
- Update the server service and upgrade the DB:
  ```bash
  docker exec $(docker ps -qf name=wf-server) prefect server database upgrade
  ```
- Copy the updated flows, loader and entrypoints:
  - Pydantic 2: `model_dump` instead of `dump`; `field_validator` instead of
    `validator`.
  - Prefect 3: `Variable` instead of `JSON`/`String` blocks; `Cron` instead of
    `CronSchedule`; `await` variables and secrets inside async functions.
  - Use the new loader with a `schedules` array (not a single `schedule`) and
    workers instead of queues.
- Update the system and integration worker services.

---

## BETA 10.1 — `v0.10.1`

Released 2026-04-30. Patch on top of `v0.10.0` (2 commits).

### Improvements and Bugfixes

- Make the maximum number of lines per field configurable, to work around
  printer quirks (`3ddf3274`).
- Set the default max field lines to 99 (`21f2b2df`).

### Upgrade Procedure

None — drop-in upgrade from `v0.10.0`.

---

## BETA 10.2 — `v0.10.2`

Released 2026-05-29. 52 commits since `v0.10.1`.

### New Features

#### Sparkplug B integration

- New on-premise edge stack — Sparkplug B bridge, simulator, historian and
  `deploy/compose/sparkplug.yaml` topology — feeding MQTT Sparkplug B device
  data through the bridge into NATS and on into the platform. Opt-in: existing
  deployments are unaffected unless the new compose file is started
  (`f44e762b`).

#### Event-sourced work order updates

- `PATCH /work-order` now goes through a `WorkOrderUpdatedEvent`, so updates
  participate in the event chain (audit history, child events, transactional
  state) instead of being a direct write (`a7504d25`).

#### Task hard/soft delete

- Collaboration model now supports both soft-delete (default, recoverable) and
  hard-delete of tasks (`46f4f0df`).

#### Server-side error persistence

- 5xx errors are now persisted to ArangoDB with a 30-day retention window —
  usable for post-mortem investigation without trawling container logs
  (`ef52f39e`).

#### Documentation site

- VitePress-based public docs site, including the v1.0 OSS launch documentation
  (Phases 2-4), v1.1 restructure, and operations runbooks / strategy notes
  (`1cac0d57`, `ca6a9fbc`, `b2fa6024`, `33594180`, `2927c0db`).

#### Developer tooling

- New `service_update` CLI helper and a local Prefect dev guide (`11af1dab`).
- Pytest split: pure-Python tests live under `testing/pytest/tests/unit/` and
  run with no Docker; integration tests stay separate (`942c8af8`).

### Breaking Changes

- **Deploy file renamed:** `tls.yml → custom-cert.yml` (`af680e5d`). Any local
  compose overrides or deployment scripts that reference `tls.yml` must be
  updated.
- **Compose must be launched from the repo root** — paths and secrets in
  `deploy/compose/dev.yaml` are now resolved from the repo root rather than
  from the compose directory (`c3179fc2`, `f959631b`).

### Improvements and Bugfixes

- API: corrected `response_model` mismatches that caused guaranteed 500s on
  some endpoints (`0c0f9378`); API calls with no bearer token no longer crash
  (`a542c15b`).
- Production: deleting a started work order now returns 403 instead of 500
  (`f5796a51`); work-order job hydration restored in the `ProductionAdminMenu`
  quantity modal (`c4191a2d`); `next_batch_available` state management fixed
  (`e9439aea`); product code access in `delete_operation` corrected
  (`9e9872a0`).
- Webapp: prevented the heartbeat `setInterval` leak that kept timers running
  after teardown (`5b76aa21`); missing i18n task labels added and delete-button
  color corrected (`cc3b3afc`); en/it i18n keys synced between the main and
  warehouse apps (`25a10e96`).
- Printing: clicking a page now adds the field there, and new pages auto-focus
  (`01260124`); the pdfme control-bar menu renders above Quasar dialogs
  (`8beedac5`).
- TypeScript form-field spec: obsolete `required` flag removed (`abdeccba`).
- Compose: api build context made consistent with the volume mount
  (`22966e71`); the stack now also works with plain `docker compose up`
  (`f959631b`).
- CI: numerous lychee + vacuum ruleset fixes; VitePress sidebar unified to
  prevent context-switching; 156 operationIds corrected with the reference
  sidebar rebuilt; first-deploy dead-link / 404 resolved.

### Upgrade Procedure

Drop-in upgrade from `v0.10.1`, with small deployment and DB touch-ups:

1. **If you reference `tls.yml` in any custom compose override or deploy
   script, rename it to `custom-cert.yml`.**
2. **Launch compose from the repo root**, e.g.
   `docker compose -f deploy/compose/base.yaml -f deploy/compose/dev.yaml up`,
   rather than `cd deploy/compose && docker compose up`. Secret paths in
   `dev.yaml` are now repo-root-relative.
3. **Database** — the API creates these idempotently on startup, but listed
   for completeness:
   - Add the `ErrorLog` collection (5xx error persistence).
   - Add the `errorlog-ttl` TTL index on `ErrorLog.ts` with
     `expireAfter = 2592000` (30 days).
4. *(Optional)* To enable the new Sparkplug B edge stack, start it from
   `deploy/compose/sparkplug.yaml`. No changes are required for deployments
   that don't use Sparkplug.
