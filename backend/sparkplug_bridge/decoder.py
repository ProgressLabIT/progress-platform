"""Sparkplug B protobuf decoding + alias-map helpers (cache-parameter style).

Phase 2 scope (D-03/D-08):
  - Decode happy-path NBIRTH / NDATA / NDEATH / DBIRTH / DDATA / DDEATH.
  - decode_sparkplug_topic returns a routing dict for STATE topics so
    main.py can flip the host_state.state_online flag (D-03 round-trip).
  - Alias map is caller-owned: populate_aliases_from_birth, resolve_alias,
    and prune_aliases all take an alias_cache dict as their first parameter.
    main.py hydrates this dict from the sparkplug_aliases KV bucket on
    startup; KV writes for cache mutations happen in main.py.

Stays pure + synchronous: no async, no nats-py imports, no I/O.
"""
import logging

from backend.sparkplug import sparkplug_b_pb2  # regenerated bindings (Plan 01-01)

logger = logging.getLogger("sparkplug_bridge.decoder")

# The alias cache is now caller-owned (main.py hydrates it from the
# sparkplug_aliases KV bucket on startup). Helpers below take it as a
# parameter named `alias_cache` with the same shape:
#   {(group, edge, bd_seq): {alias_int: (name, datatype_name)}}


# Sparkplug B v3.0.0 message types we decode in Phase 2.
# STATE is handled separately via a dedicated routing branch in decode_sparkplug_topic.
_DECODE_MSG_TYPES = {"NBIRTH", "NDATA", "NDEATH", "DBIRTH", "DDATA", "DDEATH"}


# Sparkplug datatype enum → human-readable name (per ADR-0002 type system).
# Pulled from sparkplug_b_pb2.DataType (Tahu's enum) — tightened for Phase 1's
# numeric / Boolean / String happy path.
_DATATYPE_NAMES = {
    1: "Int8", 2: "Int16", 3: "Int32", 4: "Int64",
    5: "UInt8", 6: "UInt16", 7: "UInt32", 8: "UInt64",
    9: "Float", 10: "Double", 11: "Boolean", 12: "String",
    13: "DateTime",
    # 14+ (DataSet, Bytes, File, Template) deferred to Post-Demo per ADR-0002.
}


def decode_sparkplug_topic(topic: str) -> dict | None:
    """Parse an MQTT topic string into Sparkplug components.

    Format for node/device messages:
      spBv1.0/{group_id}/{msg_type}/{edge_node_id}[/{device_id}]

    Format for STATE messages:
      spBv1.0/STATE/{host_id}

    Returns a routing dict for recognized topics, or None for unrecognized ones.
    STATE topics return {"msg_type": "STATE", "host_id": ..., group/edge/device: None}.
    """
    if not topic.startswith("spBv1.0/"):
        return None
    parts = topic.split("/")
    namespace = parts[0]

    # Check for STATE before the len < 4 guard — STATE has only 3 parts.
    if len(parts) >= 2 and parts[1] == "STATE":
        # Phase 2: route STATE echoes to main.py's host_state handler.
        # Topic format: spBv1.0/STATE/<host_id>  -> parts = ['spBv1.0', 'STATE', '<host_id>']
        # NOTE: STATE is a top-level type; group/edge/device do not apply.
        host_id = parts[2] if len(parts) > 2 else None
        return {
            "namespace": namespace,
            "msg_type": "STATE",
            "host_id": host_id,
            "group": None,
            "edge": None,
            "device": None,
        }

    if len(parts) < 4:
        return None  # malformed non-STATE topic
    group, msg_type = parts[1], parts[2]
    if msg_type not in _DECODE_MSG_TYPES:
        logger.debug("ignoring unsupported Sparkplug msg_type=%s", msg_type)
        return None
    edge = parts[3] if len(parts) > 3 else None
    device = parts[4] if len(parts) > 4 else None
    return {
        "namespace": namespace,
        "group": group,
        "msg_type": msg_type,
        "edge": edge,
        "device": device,
    }


def decode_payload(payload: bytes) -> dict:
    """Decode a Sparkplug B protobuf payload into a Python dict.

    Returns a dict with keys:
      timestamp: int (UTC ms)
      seq: int (0-255)
      metrics: list[dict] — each dict has name/alias/datatype/value/timestamp.
    The bdSeq metric is NOT specially treated here; it appears as a metric
    entry alongside others. The caller (handle_message) extracts it.
    """
    pb_payload = sparkplug_b_pb2.Payload()
    pb_payload.ParseFromString(payload)
    metrics: list[dict] = []
    for m in pb_payload.metrics:
        # Determine which value field is set — Tahu's Metric uses oneof.
        value = _extract_metric_value(m)
        metrics.append({
            "name": m.name if m.HasField("name") else None,
            "alias": m.alias if m.HasField("alias") else None,
            "datatype": _DATATYPE_NAMES.get(m.datatype, f"Unknown({m.datatype})"),
            "value": value,
            "timestamp": m.timestamp if m.HasField("timestamp") else pb_payload.timestamp,
            "is_null": m.is_null if m.HasField("is_null") else False,
            "is_historical": m.is_historical if m.HasField("is_historical") else False,
        })
    return {
        "timestamp": pb_payload.timestamp if pb_payload.HasField("timestamp") else None,
        "seq": pb_payload.seq if pb_payload.HasField("seq") else None,
        "metrics": metrics,
    }


def _extract_metric_value(m) -> object:
    """Extract a Tahu Metric oneof value, normalized for JSON serialization."""
    # Tahu's Metric exposes scalar one_of fields named after their type:
    # int_value, long_value, float_value, double_value, boolean_value, string_value,
    # bytes_value, dataset_value, template_value
    if m.HasField("int_value"):
        return m.int_value
    if m.HasField("long_value"):
        return m.long_value
    if m.HasField("float_value"):
        return m.float_value
    if m.HasField("double_value"):
        return m.double_value
    if m.HasField("boolean_value"):
        return bool(m.boolean_value)
    if m.HasField("string_value"):
        return m.string_value
    if m.HasField("bytes_value"):
        # Phase 1 happy path doesn't expect this; encode as hex string for visibility.
        return m.bytes_value.hex()
    return None  # is_null or DataSet/Template (deferred)


def populate_aliases_from_birth(
    alias_cache: dict[tuple[str, str, int], dict[int, tuple[str, str]]],
    group: str,
    edge: str,
    bd_seq: int,
    decoded: dict,
) -> None:
    """On NBIRTH/DBIRTH, register every (alias -> (name, datatype)) for this session.

    Mutates `alias_cache` in place. The caller (main.py) writes the
    resulting (group, edge, bd_seq) entry to the sparkplug_aliases KV
    bucket via kv_store.encode_doc.
    """
    key = (group, edge, bd_seq)
    table = alias_cache.setdefault(key, {})
    for m in decoded["metrics"]:
        if m["alias"] is not None and m["name"] is not None:
            table[m["alias"]] = (m["name"], m["datatype"])
    logger.info(
        "alias map populated: group=%s edge=%s bd_seq=%d count=%d",
        group, edge, bd_seq, len(table),
    )


def resolve_alias(
    alias_cache: dict[tuple[str, str, int], dict[int, tuple[str, str]]],
    group: str,
    edge: str,
    bd_seq: int,
    alias: int,
) -> tuple[str, str] | None:
    """Look up (name, datatype) for an alias under a given session.

    Returns None if the alias is unknown — caller (main.py) increments
    gaps_observed via session_state.record_gap (D-08 alias-miss counts
    toward gap budget).
    """
    return alias_cache.get((group, edge, bd_seq), {}).get(alias)


def prune_aliases(
    alias_cache: dict[tuple[str, str, int], dict[int, tuple[str, str]]],
    group: str,
    edge: str,
    bd_seq: int,
) -> bool:
    """Remove the (group, edge, bd_seq) entry from the in-memory cache.

    Called by main.py's NDEATH/DDEATH branch (per D-11 ordering — main.py
    ALSO deletes the matching key from the sparkplug_aliases KV bucket
    right before/after this call). Returns True if the entry existed and
    was removed; False if nothing to prune (no-op safe to call).
    """
    key = (group, edge, bd_seq)
    if key in alias_cache:
        del alias_cache[key]
        logger.info("alias map pruned: group=%s edge=%s bd_seq=%d", group, edge, bd_seq)
        return True
    return False
