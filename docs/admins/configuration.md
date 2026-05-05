---
title: Configuration — Admin & Integrator
description: Every PROGRESS_* environment variable for Progress Platform.
---

# Configuration

> All Progress backend services read configuration from environment variables prefixed
> with `PROGRESS_` and from Docker secrets mounted at `/run/secrets/`.

The following table is auto-extracted from `backend/api/utils/config.py` at build
time by `scripts/extract_config.py`. New fields appear here automatically on every push.

<!--@include: ../public/config-metadata.md-->

## Environment file precedence

Pydantic Settings reads configuration in this order (last wins):

1. Hardcoded class defaults.
2. `.env` file (development only — not present in production).
3. Environment variables (Compose `environment:` blocks).
4. Docker secrets at `/run/secrets/{name}` (production).

## Related

- [Deployment](/admins/deployment) — which secrets and volumes to create before deploying
- [Operations](/admins/operations) — verifying configuration at runtime
