# CustomData Collection — Design Spec

## Problem

Prefect flows and custom reports need configurable data (thresholds, mappings, lists, JSON objects). Currently this lives in Prefect variables/blocks, forcing users into the Prefect UI. This creates a fragmented admin experience.

## Solution

Add a `CustomData` ArangoDB collection with full CRUD exposed through the main webapp's admin section. Flows query it directly via AQL (they already connect to ArangoDB).

**Not related to** `CustomListValue`, which serves custom form field dropdowns.

## Data Model

**Collection:** `CustomData` (document, not edge)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `_key` | string | yes | User-provided identifier. Validated: `^[a-z][a-z0-9_]*$`, max 64 chars. |
| `value` | any JSON | yes | Scalar, object, or array — any valid JSON |
| `description` | string | no | Human-readable purpose of this record |

No timestamps, no `name` field, no org scoping. The `_key` is the identifier, `description` provides human context.

### Key Validation

Backend validates `_key` matches `^[a-z][a-z0-9_]*$` with max length 64 on all writes. Rejects with 422 if invalid. Frontend mirrors validation inline (shows error before submit).

## Backend

### Model

New file: `backend/api/models/custom_data.py`

```python
from backend.api.models.base_models import ArangoDocument

class CustomData(ArangoDocument):
    value: Any  # any valid JSON
    description: str | None = None
```

### Endpoints

New file: `backend/api/endpoints/custom_data.py`, mounted at `/custom-data` in `main.py`.

All endpoints require admin authentication via `Depends(auth.verify_token)` + admin role check.

| Method | Path | Body | Returns | Description |
|--------|------|------|---------|-------------|
| GET | `/custom-data` | — | `list[CustomData]` | List all records. Optional `search` query param filters by `_key` and `description`. |
| GET | `/custom-data/{key}` | — | `CustomData` | Single record by `_key`. 404 if not found. |
| PUT | `/custom-data/{key}` | `{ value, description? }` | `CustomData` | Upsert — creates if missing, updates if exists. Validates `_key` format (422 if invalid). |
| DELETE | `/custom-data/{key}` | — | `{ message }` | Delete record. 404 if not found. |

### Implementation Pattern

Direct DB operations (no events), matching `CustomListValue` and `Config` patterns:

- `db.collection('CustomData')` for all operations
- AQL queries for list/search
- `collection.insert()` / `collection.replace()` / `collection.delete()` for mutations
- Standard `APIResponse` wrapper for responses

### Registration

Add router to `backend/api/main.py` alongside existing endpoint imports.

## Database Init

### Production

`deploy/scripts/db_init.py` — add to collections list:

```python
Collection(name='CustomData', indexes=[])
```

No indexes needed beyond default `_key` — collection will be small and primarily accessed by key.

### Test Schema

`testing/pytest/conftest_helpers/schema.py` — add matching collection definition.

## Frontend

### View Component

New file: `webapps/main/src/views/CustomDataLibrary.vue`

**Layout:** Master-detail, matching existing library views (FormFieldLibrary, IssueTypeLibrary, etc.)

- **Left panel (list):**
  - Search/filter input at top
  - List of records showing `_key` and truncated `description`
  - "Add" button to create new record
  - Click selects record, shows detail on right

- **Right panel (detail):**
  - `_key` field — text input on create (with inline validation: `^[a-z][a-z0-9_]*$`, max 64), read-only on edit
  - `description` — textarea
  - `value` — CodeMirror 6 JSON editor with syntax highlighting and validation
  - Save button (creates or updates via PUT)
  - Delete button with confirmation dialog

### JSON Editor

Use CodeMirror 6 (already in project dependencies) with:
- `@codemirror/lang-json` for syntax highlighting
- JSON parse validation before save (prevent invalid JSON)
- Reasonable default height, resizable

### Routing

Add route as child of admin section in router config:
- Name: `customDataLibrary`
- Path: `custom-data`
- Component: `CustomDataLibrary.vue`

### Admin Section

`webapps/main/src/views/AdminSection.vue` — add `'customDataLibrary'` to `adminViews` array.

### i18n

Add translation key `views.customDataLibrary` with label (e.g., "Custom Data").

## Prefect Flow Access

No new workflow code needed. Flows already connect to ArangoDB via `backend/workflow/flows/utils.py`. Access pattern:

```python
db = get_db()  # existing util
record = db.collection('CustomData').get('my_config_key')
value = record['value']
```

## Scope Exclusions

- No event system integration (no EventType, no NATS notifications)
- No Kafka publishing
- No audit trail (can add later if needed)
- No import/export
- No versioning of values
- No org-scoping (single-tenant assumption, matching Config pattern)
