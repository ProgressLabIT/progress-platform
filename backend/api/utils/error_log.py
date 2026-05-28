"""
Persist server-side (5xx) HTTP failures to ArangoDB for post-hoc inspection.

Two FastAPI exception handlers (registered in main.py) capture both failure
patterns in this codebase: endpoint-raised ``HTTPException(500, ...)`` and
truly unhandled exceptions. Each failure is written to the ``ErrorLog``
collection with the endpoint, (redacted) payload, error, traceback, timestamp
and user. A TTL index on the numeric ``ts`` field expires rows after 30 days.

Logging is best-effort: an insert failure must never break the request, so
every persistence path is guarded and only warns on failure.
"""

import json
import logging
import time
import traceback

import jwt
from fastapi.exception_handlers import http_exception_handler as default_http_exception_handler
from starlette.requests import Request
from starlette.responses import JSONResponse

from utils import auth
from utils.config import get_config
from utils.db import db
from utils.dt import timestamp

logger = logging.getLogger("error_log")

COLLECTION = "ErrorLog"
RETENTION_SECONDS = 30 * 24 * 60 * 60  # 30 days
MAX_PAYLOAD_BYTES = 64 * 1024  # skip large/binary bodies

# Request fields (case-insensitive) whose values must never be persisted.
SENSITIVE_KEYS = {
  "password",
  "old_password",
  "new_password",
  "current_password",
  "token",
  "access_token",
  "refresh_token",
  "secret",
  "jwt",
  "authorization",
  "cookie",
  "signature",
}

REDACTED = "***REDACTED***"


def _redact(obj):
  """Recursively copy ``obj`` replacing any sensitive key's value with a marker."""
  if isinstance(obj, dict):
    return {
      k: (REDACTED if isinstance(k, str) and k.lower() in SENSITIVE_KEYS else _redact(v))
      for k, v in obj.items()
    }
  if isinstance(obj, list):
    return [_redact(v) for v in obj]
  return obj


def _extract_user_key(request: Request):
  """Best-effort user `_key` from the Bearer token. Never raises; no DB check."""
  try:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("bearer "):
      return None
    token_str = header.split(" ", 1)[1]
    claims = jwt.decode(
      token_str,
      get_config().jwt_secret,
      algorithms=[auth.ALGORITHM],
      options={"verify_exp": False},
    )
    return claims.get("sub")
  except Exception:
    return None


def _safe_payload(request: Request):
  """Redacted JSON body, or None for non-JSON / large / unparsed / multipart bodies."""
  try:
    body = getattr(request, "_body", None)
    if not body:
      return None
    if "application/json" not in request.headers.get("content-type", ""):
      return None
    if len(body) > MAX_PAYLOAD_BYTES:
      return None
    return _redact(json.loads(body))
  except Exception:
    return None


def ensure_collection():
  """Idempotently create the ErrorLog collection and its 30-day TTL index.

  Covers existing/dev databases provisioned before this collection was added to
  deploy/scripts/db_init.py. Safe to call on every startup.
  """
  try:
    if not db.has_collection(COLLECTION):
      db.create_collection(COLLECTION)
    collection = db.collection(COLLECTION)
    if not any(idx.get("name") == "errorlog-ttl" for idx in collection.indexes()):
      collection.add_index(
        dict(type="ttl", fields=["ts"], name="errorlog-ttl", expireAfter=RETENTION_SECONDS)
      )
  except Exception:
    logger.warning("Failed to ensure ErrorLog collection/index", exc_info=True)


def _record(request: Request, status_code: int, error, tb):
  """Insert one error document. Fully guarded — never propagates an exception."""
  try:
    db.collection(COLLECTION).insert(
      dict(
        endpoint=request.url.path,
        method=request.method,
        query=_redact(dict(request.query_params)),
        payload=_safe_payload(request),
        user_key=_extract_user_key(request),
        status_code=status_code,
        error=error,
        traceback=tb,
        timestamp=timestamp(),  # ISO 8601 — human-readable
        ts=time.time(),         # epoch seconds — TTL index field
      )
    )
  except Exception:
    logger.warning("Failed to persist ErrorLog entry", exc_info=True)


async def http_exception_handler(request: Request, exc):
  """Log 5xx HTTPExceptions, then defer to FastAPI's default response handling."""
  if exc.status_code >= 500:
    detail = exc.detail
    tb = detail if isinstance(detail, str) else repr(detail)
    _record(request, exc.status_code, error=str(detail), tb=tb)
  return await default_http_exception_handler(request, exc)


async def unhandled_exception_handler(request: Request, exc):
  """Log a truly unhandled exception and return an opaque 500 (no trace leak)."""
  tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
  _record(request, 500, error=str(exc), tb=tb)
  return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
