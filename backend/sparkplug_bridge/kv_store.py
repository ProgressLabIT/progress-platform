"""JetStream KV bootstrap + hydration for the sparkplug bridge.

Owns all KV bucket access. The four buckets are locked by ADR-0002:

  - sparkplug_sessions   key: "<group>.<edge>"               value: see SCHEMA below
  - sparkplug_aliases    key: "<group>.<edge>.<bd_seq>"      value: {"aliases": {alias_int: [name, type]}}
  - sparkplug_last_seq   key: "<group>.<edge>"               value: {"seq": int, "ts_utc_ms": int}
  - sparkplug_last_values key: "<group>.<edge>[.<device>].<name>" value: {"value", "type", "ts_utc_ms", "quality"}

All values are JSON-encoded bytes. All documents carry `schema_version: 1`
(a bump to 2 is required for any breaking shape change — see RESEARCH §8).

Module is bridge-local. Do NOT add KV logic to backend/api/utils/nats_client.py.
"""
import json
import logging
from typing import Any

import nats.js.api
import nats.js.errors
from nats.js.client import JetStreamContext
from nats.js.kv import KeyValue

logger = logging.getLogger("sparkplug_bridge.kv_store")

# Schema version — every KV document carries this. Bump to 2 if any field is
# renamed, removed, or has its type changed. Adding new optional fields is
# backward-compatible and does NOT require a bump.
SCHEMA_VERSION = 1

# Bucket name constants — locked by ADR-0002 § "Retention and KV state".
BUCKET_SESSIONS = "sparkplug_sessions"
BUCKET_ALIASES = "sparkplug_aliases"
BUCKET_LAST_SEQ = "sparkplug_last_seq"
BUCKET_LAST_VALUES = "sparkplug_last_values"

_ALL_BUCKETS = (BUCKET_SESSIONS, BUCKET_ALIASES, BUCKET_LAST_SEQ, BUCKET_LAST_VALUES)


async def ensure_kv_bucket(js: JetStreamContext, bucket: str, history: int = 1) -> KeyValue:
    """Idempotent: creates bucket if absent, binds to existing if present.

    Per RESEARCH §1 verified pattern: APIError on STREAM.CREATE for an
    existing-with-compatible-config bucket does not occur in practice
    (server returns OK); the except clause handles unexpected rejections
    by binding to the existing stream instead.
    """
    try:
        return await js.create_key_value(
            nats.js.api.KeyValueConfig(bucket=bucket, history=history)
        )
    except nats.js.errors.APIError:
        return await js.key_value(bucket)


async def ensure_buckets(js: JetStreamContext) -> dict[str, KeyValue]:
    """Create or bind all four sparkplug KV buckets at startup.

    Returns a dict keyed by bucket name. Logs one info line per bucket.
    Safe to call repeatedly (idempotent — see ensure_kv_bucket).
    """
    result: dict[str, KeyValue] = {}
    for name in _ALL_BUCKETS:
        kv = await ensure_kv_bucket(js, name)
        result[name] = kv
        logger.info("kv bucket ready: %s", name)
    return result


async def _read_all(kv: KeyValue) -> dict[str, dict]:
    """Read every key in a KV bucket into a dict[key, parsed-json-doc].

    Uses watchall(include_history=False); breaks on the None sentinel that
    signals 'initial snapshot delivered'. Returns {} on an empty bucket.
    """
    cache: dict[str, dict] = {}
    try:
        watcher = await kv.watchall(include_history=False)
    except nats.js.errors.NotFoundError:
        return cache
    try:
        async for entry in watcher:
            if entry is None:
                break
            if entry.value:
                try:
                    cache[entry.key] = json.loads(entry.value)
                except json.JSONDecodeError:
                    logger.warning(
                        "kv decode failed for %s/%s — skipping", kv, entry.key
                    )
    finally:
        await watcher.stop()
    return cache


async def hydrate_sessions(kv: KeyValue) -> dict[str, dict]:
    """Read all entries from sparkplug_sessions into {(group.edge): doc}."""
    return await _read_all(kv)


async def hydrate_aliases(kv: KeyValue) -> dict[str, dict]:
    """Read all entries from sparkplug_aliases into {(group.edge.bd_seq): doc}."""
    return await _read_all(kv)


async def hydrate_last_seq(kv: KeyValue) -> dict[str, dict]:
    """Read all entries from sparkplug_last_seq into {(group.edge): doc}."""
    return await _read_all(kv)


async def hydrate_last_values(kv: KeyValue) -> dict[str, dict]:
    """Read all entries from sparkplug_last_values into {metric_id: doc}."""
    return await _read_all(kv)


def encode_doc(doc: dict[str, Any]) -> bytes:
    """JSON-encode a KV value, stamping schema_version if absent.

    Caller passes domain fields; this helper guarantees `schema_version: 1`
    is present without callers having to remember.
    """
    if "schema_version" not in doc:
        doc = {"schema_version": SCHEMA_VERSION, **doc}
    return json.dumps(doc).encode()
