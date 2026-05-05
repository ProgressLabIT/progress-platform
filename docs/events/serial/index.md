---
title: Serial Events
description: Serial domain events - Progress Platform Events Reference.
---

# Serial Events

Serial-domain events manage the lifecycle of traceable serial units: creation,
code assignment, parent-child linking, release, and deletion. All serial events
extend `BaseSerialEvent`, which publishes to `progress.notification.serial`
after transaction commit.

## Events

| Event | EventType |
|-------|-----------|
| [SerialCreatedEvent](/events/serial/serial-created) | `SERIAL_CREATED` |
| [SerialDeletedEvent](/events/serial/serial-deleted) | `SERIAL_DELETED` |
| [SerialLinkedEvent](/events/serial/serial-linked) | `SERIAL_LINKED` |
| [SerialReleasedEvent](/events/serial/serial-released) | `SERIAL_RELEASED` |
| [SerialUnlinkedEvent](/events/serial/serial-unlinked) | `SERIAL_UNLINKED` |
| [SerialUpdatedEvent](/events/serial/serial-updated) | `SERIAL_UPDATED` |
