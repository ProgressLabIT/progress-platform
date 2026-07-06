# Serial Management

Serials are unique identifiers for individual product units, enabling full traceability through the manufacturing process.

## Serial Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   CREATED   │────▶│   UPDATED   │────▶│  RELEASED   │────▶│   DELETED   │
│             │     │  (N times)  │     │             │     │ (optional)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │   LINKED    │ (component serials)
                    │  UNLINKED   │
                    └─────────────┘
```

### Events

| Event | Purpose |
|-------|---------|
| `SerialCreatedEvent` | Creates a new serial record, optionally with initial data from work order |
| `SerialUpdatedEvent` | Updates serial code, data fields, or unreleases the serial |
| `SerialReleasedEvent` | Marks serial as released (production complete) |
| `SerialLinkedEvent` | Links a component serial to a parent serial (BOM traceability) |
| `SerialUnlinkedEvent` | Removes a component serial link |
| `SerialDeletedEvent` | Soft-deletes a serial |
| `SerialBookedEvent` | Books serials for a job |

## Data Model

### Serial Document (`models/serial.py`)

```python
class Serial(ArangoDocument):
  code: str | None           # Human-readable identifier (e.g., "SN-2024-0001")
  product_key: str           # Reference to Product
  wo_key: str | None         # Reference to WorkOrder
  counter_key: str | None    # Counter for auto-generating codes
  created: datetime          # Timestamp
  released: datetime | None  # When production completed
  data: list[SerialFormFieldValue]  # Form field values collected during production
  deleted: str | bool        # False or event_key of deletion
```

### Serial Form Field Value (`models/form.py`)

Each field in `serial.data` contains:

```python
class SerialFormFieldValue:
  form_field_key: str       # Reference to form field definition
  custom_field_key: str     # Reference to custom field type
  label: str | None
  hint: str | None
  mandatory: bool | None
  value: Any | None         # The actual value
  batch_key: str | None     # Which batch collected this data
  step_key: str | None      # Which step collected this data
  phase_key: str | None     # Which phase collected this data
  last_updated: str | None  # Event key of last update
```

## Serial Data Updates

### How Data is Merged (`SerialUpdatedEvent._merge_serial_data`)

When updating serial data, the system performs a **merge operation**:

1. **Existing fields** are preserved
2. **Changed values** are updated (with `last_updated` timestamp)
3. **New fields** are added to the serial data

This allows production steps to progressively add data to serials as they move through phases. For example:
- Phase 1 collects inspection data → saved to serial
- Phase 2 collects test results → added to serial
- Phase 3 collects packaging info → added to serial

**Important:** The merge uses `form_field_key` as the unique identifier. Multiple values for the same field key will result in the latest value being kept.

### Manual Field Addition

Users can manually add custom fields to serials via the `SerialDetailForm.vue` component:

1. Click "Add Field" button (visible only in edit mode)
2. Search and select from existing custom fields
3. The field is added locally with:
   - `form_field_key` = `custom_field_key` (since it's a manual addition without a form definition)
   - `label` from custom field's `default_label` or `name`
   - `hint` from custom field's `default_hint`
   - `value` = `null` (to be filled by user)
4. On save, the new field is sent to backend and merged via `SerialUpdatedEvent`

**Note:** Fields already present on the serial are excluded from the search to prevent duplicates.

### Code Protection

Serial code changes can be protected via config:
- `Config['allow_serial_code_edit']` controls whether codes can be changed after initial assignment
- Empty string (`""`) can be used to clear a code
- Code uniqueness is enforced per product

## Counter Configuration

Counters auto-generate serial codes using a template system.

### Counter Model (`models/counter.py`)

```python
class Counter(ArangoDocument):
  name: str              # Human-readable name
  next_tick: int = 1     # Current counter value (auto-incremented)
  template: list[str]    # Code template tokens
  frequency: str | None  # Reset frequency (e.g., "year")
  reset_date: datetime   # Next reset date
```

### Template Tokens

| Token | Description | Example |
|-------|-------------|---------|
| `%y` | 2-digit year | `25` |
| `%Y` | 4-digit year | `2025` |
| `%m` | Month | `01` |
| `%d` | Day | `14` |
| `#N` | Counter with N digits (zero-padded) | `#5` → `00042` |
| `text` | Fixed text | `SN-`, `-` |

**Example:** Template `["SN-", "%Y", "-", "#5"]` produces `SN-2025-00042`

### Counter Reset

Counters can auto-reset based on frequency:
- When `DATE_NOW() > reset_date`, the counter resets to 1
- `reset_date` advances by the configured `frequency`

### When Codes are Generated

| Scenario | Trigger |
|----------|---------|
| Product has `serial_code_on_creation = True` | Code generated at serial creation |
| Serial released without code | Code generated at `BatchCompletedEvent` (first phase) |
| Manual assignment | Code provided via `SerialUpdatedEvent` |

## Integration Points

### Production Flow

1. **Batch Start** (`BatchStartedEvent`): Creates serials from work order with initial `serial_fields`
2. **Step Completion** (`StepCompletedEvent`): Form data collected but not yet on serial
3. **Batch Completion** (`BatchCompletedEvent`): 
   - Calls `_prepare_serial_data()` to gather all step data
   - Calls `SerialUpdatedEvent` to merge data onto each serial
   - Calls `SerialReleasedEvent` if last phase

### Active Batch Changes (`ActiveBatchChangedEvent`)

When batch quantity changes during production:

**First Phase (with traceability):**
- **Quantity increased:** New serials are created via `_create_serial_records()`
  - If `serial_code_on_creation` is enabled, codes are generated immediately
  - Otherwise, serials are created without codes (assigned later)
- **Quantity decreased:** Excess serials are deleted via `DELETE_BATCH_SERIALS` query
  - Deletes serials without codes first, ordered by creation date
  - Cleans up `batch_serial` and `contains` edge links

**Following Phases (with traceability):**
- Rebooks WIP serials via `WIPBookedEvent` with the new serial selection
- Cleans up unconfirmed component links for serials no longer in batch

**Without traceability:**
- Only WIP quantity booking/unbooking (no serial documents involved)

### Batch Cancellation (`BatchCanceledEvent`)

When a batch is canceled, serial handling depends on the phase:

**First Phase (with traceability):**
- All batch serials are **deleted** via `SerialDeletedEvent`
- `batch_serial` edge records are removed
- Component links (`contains`) are removed

**Following Phases (with traceability):**
- Serials are **preserved** (they existed before this phase)
- `batch_serial` edge records are removed (unlinking from canceled batch)
- Component links for this batch are removed
- Step data is NOT removed from serials (it's only saved on batch completion)

**Without traceability:**
- Component serial links are unlinked via `SerialUnlinkedEvent`
- No serial documents to delete

### Traceability & Component Genealogy

- Serials are linked into parent-child genealogy via `SerialLinkedEvent`; the link lives in the **`contains`** edge collection (`_from` = parent, `_to` = `Serial/<child>`). `SerialTreeNode` models the hierarchy.
- **Two-step linking.** During execution the frontend stages *temporary* (unconfirmed) `contains` edges via `PUT /batch/{batch_key}/serial-temp-links` (`create_temporary_link`, `endpoints/traceability.py`). At batch completion `BatchCompletedEvent._handle_batch_serials` reads them through `batch_component_serials_map` and emits one `SerialLinkedEvent` per child to **confirm** them (`confirmed=True`). The per-serial consumption movements in `_process_consumption` are driven by the **same map**, so a confirmed link and its consumption movement always come as a pair within the one `BATCH_COMPLETED` event group.
- **`SerialLinkedEvent` stores the child under `child_serial_key`, not `serial_key`.** Any serial-scoped event query (`FILTER e.serial_key == k`) is **blind to genealogy events** — filter on `child_serial_key` / `parent_serial_key`, or read the `contains` edge directly.

#### The `"components"` sentinel (gotcha)

`parent_serial_key` accepts the literal string **`"components"`** (and `None`) to mean *"link to the batch, not to a parent serial"* — the path used when the job **output has no traceability** (documented on `SerialLink._from`, `models/serial.py`). Frontend origin: `store/traceability.js` fabricates a synthetic tree node `{_key:'components', children:[…]}`, and `SerialBomForm.vue` emits `parentSerialKey: batchSerials[index]?._key ?? 'components'`.

**Risk — orphaned genealogy in mixed batches.** `create_temporary_link` historically decided batch-vs-parent **all-or-nothing over the whole payload**:

```python
connect_to_batch = set(link.parent_serial_key for link in links) in [set(['components']), set([None])]
...
if connect_to_batch:        # only when EVERY link is batch-level
    for link in links: link.parent_serial_key = f'Batch/{batch_key}'
```

The serial-existence check in the same endpoint also *excludes* `'components'` (`- set([None, 'components'])`), assuming it will always be rewritten. So if a single component row resolves to `'components'` (e.g. `batchSerials[index]` momentarily `undefined` in an otherwise-traceable batch — index past the declared output serials, or a load race) **while its siblings carry a real parent serial**, the parent set is heterogeneous → `connect_to_batch = False` → the sentinel is **neither rewritten nor validated**. It is inserted verbatim, and `SerialLinkedEvent.apply` (parent ≠ `None` branch) writes `_from = 'Serial/components'` — a child of a **phantom serial**, attached to neither the batch nor the real parent.

> Observed 2026-06-26: batch `47404498` — two components linked to parent serial `47404500`, one (serial `26024920` / code `3793`) orphaned under `Serial/components`.

**Fix (backend, contract):** a batch's component links must all share one parent type. Reject a mixed payload (real parent serials **and** the `None`/`'components'` sentinel together) with **422** — it is always a client bug (typically a stale/undefined output-serial index in the UI). Only a homogeneous batch-level payload is rewritten to `Batch/<batch_key>`:

```python
parents = set(link.parent_serial_key for link in links)
real_parents = parents - {None, 'components'}
batch_level = bool(parents & {None, 'components'})
if real_parents and batch_level:
    raise HTTPException(422, "Mixed parent links: ... must share the same parent type.")
...
if batch_level:        # homogeneous → every link is the sentinel
    for link in links: link.parent_serial_key = f'Batch/{batch_key}'
```

Fails loud instead of silently linking a stray component to the batch, so the bad UI state surfaces immediately rather than corrupting genealogy. The frontend should *also* guard the `?? 'components'` fallback so it cannot fire for a missing index in a traceable batch (stops the bad payload at the source; until then, operators hitting this get a hard 422 on save — correct, better than an orphan).

**Existing-data remediation** is not automatic — `contains` edges and `SERIAL_LINKED` events are immutable. A mislinked serial needs a corrective `SERIAL_UNLINKED` + `SERIAL_LINKED` (to `Batch/<batch_key>`, or to the intended parent serial).

#### Regenerated output serial → phantom-complete BOM line (gotcha)

A **distinct** genealogy-corruption mode from the `"components"` sentinel above. A temporary `contains` edge carries a `batch_key` **and** a parent output serial (`_from = Serial/<parent>`). When a batch's output serials are regenerated **in place** — same `batch_key`, new `Serial` — via qty change (`ActiveBatchChangedEvent`), wip re-book (`WIPBookedEvent.book_wip_serials`), etc., the *old* temp links keep the batch_key but now point at a parent serial the batch no longer produces.

Two consumers then disagree — the source of the "flag works backwards" report:

| Consumer | Filter | Effect on an orphan |
|---|---|---|
| `GET_WORKING_JOB_DATA` `declared_serials` (`utils/production.py`) → the green ✓ / red asterisk icon (`WorkSessionBom.vue`) | `component_key` + `phase_key` + `batch_key` (**historically parent-agnostic**) | **counts** it → line shows complete |
| `SerialBomForm.getLineSerials` (dialog) | above **plus** `parent_serial_key == current output serial` | **hides** it → dialog empty |

So a line reads complete while the dialog shows nothing; on save, `saveSerialLinks` re-sends the orphan (it seeds `bom_serials` from `declared_serials`) and `create_temporary_link`'s `delete_match(batch_key)` + reinsert re-persists it.

> Observed 2026-07-03: batch `47886960` — current output serial `47886962`, component `2000474` still linked to defunct output serial `47886699`.

**Fix (two layers):**
1. **Count is now parent-aware** — `declared_serials` only counts links whose `_from` is a **current** batch output serial (`OUTBOUND Batch/<key> batch_serial`) or the batch-level sentinel (`Batch/<key>`). This aligns the icon with the dialog and neutralizes existing orphans with no migration (they stop counting; the next temp-save also drops them).
2. **Source paths prune** — the shared `SerialQueries.PRUNE_ORPHANED_COMPONENT_LINKS` (derives current serials from `batch_serial` edges, removes unconfirmed non-sentinel links to defunct parents) runs after serials settle in `ActiveBatchChangedEvent`, `WIPBookedEvent.book_wip_serials`, and `BatchCanceledEvent._handle_traceability`. (`ActiveBatchChanged` previously pruned inline against the *client-passed* `batch_serials` list — fragile: keys-vs-codes mismatch, empty on auto-serialled first phase; the edge-derived query replaces it. `JobResetEvent._unlink_components` already deletes all temp links by `batch_key`, so it needs no change.)

**Existing-data remediation:** `deploy/scripts/remediate_orphaned_component_links.aql` (dry-run RETURN first, then REMOVE) — safe to run globally: touches only unconfirmed temp links whose parent isn't a current batch output serial.

## Configuration

### System Config

| Config Key | Description |
|------------|-------------|
| `allow_serial_code_edit` | Whether serial codes can be changed after assignment |

### Product Settings

| Field | Description |
|-------|-------------|
| `traceability_level` | Enables serial tracking for this product (required for serial creation) |
| `serial_code_on_creation` | If true, serial code is generated immediately at creation; otherwise at release |
| `counter_key` | Reference to Counter for auto-generating serial codes |

## Notifications

Serial events publish to Kafka topic `serials` with notification types:
- `CREATED`, `UPDATED`, `DELETED`, `FINALIZED`, `ERROR`

Error codes: `SERIAL_ALREADY_PRESENT`, `COUNTER_NOT_DEFINED`, `SERIAL_CODE_EDIT_NOT_ALLOWED`, `EXCEPTION`
