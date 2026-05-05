---
title: Admin Events
description: Admin domain events - Progress Platform Events Reference.
---

# Admin Events

Admin-domain events extend `BaseAdmin`, which itself extends `BaseProductionEvent`.
They are used for operator-assisted corrections and overrides on production jobs.
`BaseAdmin.post_processing()` calls `update_work_order()` and flags the job with
a `forced` marker. The `ExtraUpdateRequestedEvent` does not override
`_notification_subtopic`, so it produces no NATS notification after commit.

## Events

| Event | EventType |
|-------|-----------|
| [ExtraUpdateRequestedEvent](/events/admin/extra-update-requested) | `EXTRA_UPDATE_REQUESTED` |
