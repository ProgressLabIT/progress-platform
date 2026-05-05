---
title: CountImportedEvent
description: COUNT_IMPORTED — Progress Platform Events Reference
---

# CountImportedEvent

**EventType:** `COUNT_IMPORTED`
**Domain:** inventory
**NATS subject:** `progress.notification.inventory`

Imports count records from an uploaded spreadsheet file into an inventory count
session. Creates `inventory_count_record`, `Position`, and `Serial` documents
as needed, updates `is_in_position` quantities, and records import statistics
(rows total, added, updated, discarded, and any ignored columns).

## Trigger

**Triggered by:** [POST /event](/api/traceability/post-event) (universal event dispatcher)

Created directly in `backend/api/endpoints/counting.py` at
`POST /inventory/count-record/import` (execute mode only — dry-run requests
do not emit this event).

## Preconditions

- `InventoryCountSession` exists with key `info.count_session_key`
- Import file identified by `info.import_file_key` has been uploaded

## State Changes (Transaction)

**Collections:** `inventory_count_record`, `Product`, `Position`, `Serial`,
`is_in_position`, `InventoryCountSession`

- `inventory_count_record` records inserted for each import row
- `Position` documents created if not present
- `Serial` documents created for new serial codes
- `is_in_position` quantities set per import data
- `InventoryCountSession` updated with import result stats

## Side Effects (post_processing)

Inherits `post_processing()` from `BaseInventoryEvent`:
- Publishes to `progress.notification.inventory`

## InfoModel Fields

| Field | Type | Description |
|-------|------|-------------|
| `count_session_key` | `str` | Key of the target inventory count session |
| `import_mode` | `str` | Import mode: `add`, `replace`, or `update` |
| `import_file_key` | `str` | Key of the uploaded import file |
| `import_filename` | `str` | Original filename for audit trail |
| `rows_total` | `int` | Total rows in the import file |
| `rows_added` | `int` | Rows that created new count records |
| `rows_updated` | `int` | Rows that updated existing count records |
| `rows_discarded` | `int` | Rows skipped due to errors or duplicates |
| `ignored_columns` | `list[str]` | Column headers in the file not recognised by the importer |

## Related Events

_None._

## Source

[`CountImportedEvent` on GitHub](https://github.com/ProgressLabIT/progress-platform/blob/DEV/backend/api/events/inventory/count_imported.py)
