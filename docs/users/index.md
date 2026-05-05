---
title: User Documentation
description: Progress Platform — user walkthroughs of the main webapp and warehouse SPA.
---

# User Documentation

Progress Platform is a Manufacturing Execution System (MES) that models work
orders, jobs, batches, steps, inventory positions, and stock-take sessions on
an event-sourced spine. Every state change — a job started, a batch closed, a
movement completed — flows through a typed event applied inside an ArangoDB
transaction, so the audit trail and the live state are the same artefact. The
platform also publishes those changes upstream as Sparkplug B over MQTT,
which is why the v1.0 launch ships with documentation aimed at the
**Industry-4.0 consultants** integrating Progress with their UNS and shop-floor
fleets.

This section walks through the operator-facing surfaces of the main webapp
and the touch-friendly warehouse SPA. It tracks what users see in the drawer;
it does not duplicate the API or the events reference.

## Walkthroughs by module

- [Production](/users/production) — work orders, jobs, batches, steps
- [Inventory](/users/inventory) — positions, movements, hierarchy
- [Counting](/users/counting) — count sessions, count records
- [User Hub](/users/user-hub) — assignments, jobs feed, preferences
- [Warehouse mobile app](/users/warehouse) — barcode-scanning SPA for floor ops
- [Coverage philosophy](/users/coverage) — what's in v1, what isn't

## Where to go next

- Integrators consuming the REST surface start at the [API reference](/api/).
- Operators bootstrapping a stack from the CLI start at [`progress init`](/cli/init).
- Deployers wiring Compose, secrets, and Traefik start at [Deployment](/admins/deployment).
