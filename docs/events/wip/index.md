---
title: WIP Events
description: WIP domain events - Progress Platform Events Reference.
---

# WIP Events

Work-In-Progress (WIP) events track material booked, declared, and removed
across production phases. WIP events are production-adjacent: they extend
`BaseProductionEvent` (or its subclasses), so they publish to
`progress.notification.production` after commit.

## Events

| Event | EventType |
|-------|-----------|
| [WIPBookedEvent](/events/wip/wip-booked) | `WIP_BOOKED` |
| [WIPDeclaredEvent](/events/wip/wip-declared) | `WIP_DECLARED` |
| [WIPRemovedEvent](/events/wip/wip-removed) | `WIP_REMOVED` |
| [WIPUnbookedEvent](/events/wip/wip-unbooked) | `WIP_UNBOOKED` |
