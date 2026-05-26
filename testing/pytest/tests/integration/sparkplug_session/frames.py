"""Handcrafted Tahu Sparkplug B protobuf builders for integration tests.

These pure functions return serialized protobuf ``bytes`` ready to be
published over MQTT. Used by tests in this directory (Plan 02-08) to
inject pathological frames the live simulator (ADR-0007) does not
produce — bdSeq mismatch, seq gap, alias miss, etc.

The simulator is NOT modified to add misbehavior modes (D-13).

Datatype integer codes match decoder.py _DATATYPE_NAMES:
  1 Int8, 2 Int16, 3 Int32, 4 Int64,
  5 UInt8, 6 UInt16, 7 UInt32, 8 UInt64,
  9 Float, 10 Double, 11 Boolean, 12 String, 13 DateTime
"""
from __future__ import annotations

import time
from typing import Iterable

from backend.sparkplug import sparkplug_b_pb2

# ---------------------------------------------------------------------------
# Datatype constants — explicit aliases so test code reads naturally.
# Values match decoder.py _DATATYPE_NAMES integer keys.
# ---------------------------------------------------------------------------
DT_INT8 = 1
DT_INT16 = 2
DT_INT32 = 3
DT_INT64 = 4
DT_UINT8 = 5
DT_UINT16 = 6
DT_UINT32 = 7
DT_UINT64 = 8
DT_FLOAT = 9
DT_DOUBLE = 10
DT_BOOL = 11
DT_STRING = 12
DT_DATETIME = 13

# Locked metric name for bdSeq — matches _BD_SEQ_METRIC_NAME in main.py.
BD_SEQ_NAME = "bdSeq"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _set_metric_value(m, datatype: int, value) -> None:
    """Set the appropriate Tahu Metric oneof field based on datatype int.

    Dispatches to the correct protobuf oneof field name.  The mapping is:
      int_value  : Int8, Int16, Int32, UInt8, UInt16, UInt32
      long_value : Int64, UInt64
      float_value: Float
      double_value: Double
      boolean_value: Boolean
      string_value: String / DateTime (stored as ms epoch for DateTime)
    """
    if datatype in (1, 2, 3, 5, 6, 7):   # Int8..Int32, UInt8..UInt32
        m.int_value = int(value)
    elif datatype in (4, 8):              # Int64, UInt64
        m.long_value = int(value)
    elif datatype == 9:                   # Float
        m.float_value = float(value)
    elif datatype == 10:                  # Double
        m.double_value = float(value)
    elif datatype == 11:                  # Boolean
        m.boolean_value = bool(value)
    elif datatype in (12, 13):            # String, DateTime
        m.string_value = str(value)
    else:
        raise ValueError(f"unsupported datatype int: {datatype}")


def _add_metric(
    payload,
    *,
    name: str | None,
    alias: int | None,
    datatype: int,
    value,
    timestamp_ms: int | None = None,
) -> None:
    """Append a single metric to ``payload.metrics``.

    ``name`` and ``alias`` are each optional — pass ``None`` to omit.
    ``value=None`` sets ``is_null=True`` on the metric (null value frame).
    ``timestamp_ms`` defaults to the payload timestamp when not provided.
    """
    m = payload.metrics.add()
    if name is not None:
        m.name = name
    if alias is not None:
        m.alias = alias
    m.datatype = datatype
    m.timestamp = timestamp_ms if timestamp_ms is not None else payload.timestamp
    if value is None:
        m.is_null = True
    else:
        _set_metric_value(m, datatype, value)


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def make_nbirth(
    bd_seq: int,
    seq: int = 0,
    metrics: Iterable[dict] | None = None,
    timestamp_ms: int | None = None,
) -> bytes:
    """Build a minimal NBIRTH protobuf payload.

    Always inserts a bdSeq metric (name=BD_SEQ_NAME, datatype=DT_UINT64,
    long_value=bd_seq) at position 0 in the metrics list — this is required
    by the bridge's ``_extract_bd_seq`` path.

    Args:
        bd_seq:       0-255 birth-death generation counter.
        seq:          0-255 sequence number; NBIRTH starts a session at 0.
        metrics:      List of dicts with keys: name, alias (opt), datatype, value (opt).
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes.
    """
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    payload.seq = seq
    # bdSeq metric MUST be present — the bridge's _extract_bd_seq depends on it.
    _add_metric(payload, name=BD_SEQ_NAME, alias=None, datatype=DT_UINT64, value=bd_seq)
    for spec in (metrics or []):
        _add_metric(
            payload,
            name=spec.get("name"),
            alias=spec.get("alias"),
            datatype=spec["datatype"],
            value=spec.get("value"),
        )
    return payload.SerializeToString()


def make_dbirth(
    bd_seq: int,
    seq: int,
    metrics: Iterable[dict],
    timestamp_ms: int | None = None,
) -> bytes:
    """Build a DBIRTH protobuf payload.

    Per Sparkplug B spec, DBIRTH does NOT include a bdSeq metric — bdSeq
    is on NBIRTH only.  The seq increments from the parent edge node's last
    NBIRTH seq counter.

    Args:
        bd_seq:       Retained for API symmetry; NOT added as a metric.
        seq:          Sequence number continuing from the edge node's session.
        metrics:      List of dicts with keys: name, alias (opt), datatype, value (opt).
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes.
    """
    _ = bd_seq  # Spark plug B spec: bdSeq is NOT in DBIRTH.
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    payload.seq = seq
    for spec in metrics:
        _add_metric(
            payload,
            name=spec.get("name"),
            alias=spec.get("alias"),
            datatype=spec["datatype"],
            value=spec.get("value"),
        )
    return payload.SerializeToString()


def make_ndata(
    seq: int,
    metrics: Iterable[dict],
    timestamp_ms: int | None = None,
) -> bytes:
    """Build an NDATA protobuf payload.

    Metrics typically carry aliases only (no ``name``); the bridge's
    resolve_alias path looks up the name from the alias cache populated by
    NBIRTH.  To exercise alias-miss tests, pass an alias not registered
    during NBIRTH.

    Args:
        seq:          Sequence number (must be last_seq + 1, mod 256).
        metrics:      List of dicts: alias (opt), name (opt), datatype, value (opt).
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes.
    """
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    payload.seq = seq
    for spec in metrics:
        _add_metric(
            payload,
            name=spec.get("name"),
            alias=spec.get("alias"),
            datatype=spec["datatype"],
            value=spec.get("value"),
        )
    return payload.SerializeToString()


def make_ddata(
    seq: int,
    metrics: Iterable[dict],
    timestamp_ms: int | None = None,
) -> bytes:
    """Build a DDATA protobuf payload.

    Device-data has the same wire shape as NDATA at the protobuf level —
    the difference is in the MQTT topic, not the payload.

    Args:
        seq:          Sequence number.
        metrics:      List of dicts: alias (opt), name (opt), datatype, value (opt).
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes.
    """
    return make_ndata(seq, metrics, timestamp_ms=timestamp_ms)


def make_ndeath(bd_seq: int, timestamp_ms: int | None = None) -> bytes:
    """Build a minimal NDEATH protobuf payload (LWT body).

    Per Sparkplug B v3.0.0 § 6.4.20, the NDEATH payload carries ONLY the
    bdSeq metric.  The bridge's ``_extract_bd_seq`` compares this value
    against the session's last NBIRTH bdSeq to detect stale LWT delivery
    (D-05).

    Args:
        bd_seq:       bdSeq value to embed; must match NBIRTH bdSeq for a
                      fresh death or differ to trigger the stale-NDEATH path.
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes.
    """
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    _add_metric(payload, name=BD_SEQ_NAME, alias=None, datatype=DT_UINT64, value=bd_seq)
    return payload.SerializeToString()


def make_ddeath(timestamp_ms: int | None = None) -> bytes:
    """Build a minimal DDEATH protobuf payload.

    Device-level DEATH does not carry bdSeq — bdSeq is an edge-node
    concept.  The bridge's NDEATH/DDEATH handler uses the parent edge's
    session bdSeq for staleness checks.

    Args:
        timestamp_ms: Payload timestamp epoch-ms; defaults to wallclock.

    Returns:
        Serialized protobuf bytes (payload with no metrics).
    """
    payload = sparkplug_b_pb2.Payload()
    payload.timestamp = timestamp_ms if timestamp_ms is not None else int(time.time() * 1000)
    return payload.SerializeToString()
