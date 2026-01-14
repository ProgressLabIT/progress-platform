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

### Traceability

- Serials can be linked to form parent-child relationships via `SerialLinkedEvent`
- The `contains` edge collection stores these relationships
- `SerialTreeNode` model represents the hierarchical structure

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
