#!/usr/bin/env python3
"""Export FastAPI OpenAPI schema to docs/public/openapi.json.

Runs as a pre-VitePress build step in deploy-docs.yml.
No live server, DB, or NATS required — `app.openapi()` is pure
introspection and does not fire startup handlers.
"""
import json
import os
import sys
from pathlib import Path

# Point Python at the backend package root so `from main import app` resolves.
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend" / "api"))

# pydantic-settings reads env vars at import time. All Settings fields have
# defaults, but JWT_SECRET and API_DB_PWD validate non-empty — set placeholders.
os.environ.setdefault("PROGRESS_JWT_SECRET", "build-time-placeholder")
os.environ.setdefault("PROGRESS_API_DB_PWD", "build-time-placeholder")

from main import app  # noqa: E402 — sys.path.insert must precede

schema = app.openapi()

# Pitfall 6 smoke-check: validate JSON round-trips before writing.
# Malformed JSON would surface at VitePress build time as a cryptic error.
_ = json.loads(json.dumps(schema))

out_path = REPO_ROOT / "docs" / "public" / "openapi.json"
out_path.write_text(json.dumps(schema, indent=2))
print(f"Wrote {len(schema.get('paths', {}))} paths to {out_path}")
