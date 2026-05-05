---
title: Coverage philosophy
description: What v1 of the Progress Platform documentation covers, and what we deliberately deferred.
---

# Coverage philosophy

> Breadth before depth. Every module has a page; no page has a deep tutorial.

The v1 launch documents every operator-visible surface in the main webapp and
the warehouse SPA, every public REST endpoint, every domain event, and every
`PROGRESS_*` configuration variable. It does not yet teach those surfaces with
step-by-step tutorials. A reader can confirm Progress Platform handles their
use case; they cannot yet read this site instead of attending a training
session.

## What v1 documents

- Every CLI command (`progress init`, `restore`, `tap`).
- Every top-level user module visible from the main webapp drawer (5 modules).
- The warehouse SPA, framed as the touch-friendly browser app it is today.
- Every `PROGRESS_*` environment variable, auto-extracted from source.
- The full event reference and OpenAPI surface.

## What v1 defers

- Step-by-step tutorials per module (post-launch — see REQUIREMENTS.md COV-05).
- Embedded / airgap docs distribution (REQUIREMENTS.md EMBED-01/02).
- Multi-language docs (REQUIREMENTS.md I18N-01..03).
- Polished screenshots — placeholders ship now; capture lands post-launch.
- Native warehouse app deployment (Capacitor surface is not used; warehouse runs as a browser SPA).
- Auto-generated Mermaid diagrams for all 81 events — top-10 hand-crafted only (REQUIREMENTS.md COV-02/03).
- Custom subdomain (REQUIREMENTS.md POL-01); Algolia DocSearch (POL-02); search analytics (POL-04).

## Why breadth-first

A deep tutorial on one module while three other modules have no page at all
is worse than a coarse walkthrough of every module. The launch audience —
system integrators evaluating whether Progress fits their UNS — needs to see
the whole shape of the product on day one, not master one corner of it. The
trade-off is explicit: tutorials, screencasts, and localisation queue up for
the post-launch curation cycle, while the v1 site holds the line on covering
the full surface area. That choice ties directly back to the workstream's
Core Value statement: a system integrator can understand what Progress does
without reading source code.
