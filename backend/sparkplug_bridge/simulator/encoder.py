"""pysparkplug encoder wrappers (encoder-only — NEVER import EdgeNode/Client).

Per RESEARCH §Anti-patterns: pysparkplug.EdgeNode wraps paho-mqtt synchronously
and would force a thread bridge inside the asyncio simulator. We use the dataclasses
NBirth / NData / NDeath / DBirth / DData / Metric strictly as protobuf encoders
and ship the resulting bytes via aiomqtt.
"""
from __future__ import annotations

import logging
from typing import Iterable

from aiomqtt import Will
from pysparkplug import (
    DBirth,
    DData,
    DDeath,
    DataType,
    Metric,
    NBirth,
    NData,
    NDeath,
)

from .physics import now_ms

logger = logging.getLogger("sparkplug_sim.encoder")

BD_SEQ_METRIC_NAME = "bdSeq"


def _build_bd_seq_metric(bd_seq: int, ts_ms: int | None = None) -> Metric:
    """Build the canonical bdSeq metric (Sparkplug B v3.0.0 § 6.4.16)."""
    return Metric(
        timestamp=ts_ms if ts_ms is not None else now_ms(),
        name=BD_SEQ_METRIC_NAME,
        datatype=DataType.INT64,
        value=bd_seq,
    )


def build_ndeath_will(group_id: str, edge_node_id: str, bd_seq: int) -> Will:
    """Build the LWT (NDEATH) `Will` for an aiomqtt client.

    The broker delivers this payload on unclean disconnect (Sparkplug B
    requires NDEATH with QoS=1, retain=False). `payload_bytes` MUST be `bytes`,
    not `str`, per RESEARCH §Pitfall 4.
    """
    bd_seq_metric = _build_bd_seq_metric(bd_seq)
    payload_bytes = NDeath(
        timestamp=now_ms(),
        bd_seq_metric=bd_seq_metric,
    ).encode(include_dtypes=True)
    assert isinstance(payload_bytes, bytes), "NDEATH payload must be bytes (Pitfall 4)"
    return Will(
        topic=f"spBv1.0/{group_id}/NDEATH/{edge_node_id}",
        payload=payload_bytes,
        qos=1,
        retain=False,
    )


def build_nbirth_payload(metrics_with_aliases: Iterable[tuple[str, DataType, object, int]],
                         seq: int, bd_seq: int) -> bytes:
    """Build NBIRTH bytes per ADR-0007 § Aliases and birth ordering.

    Args:
        metrics_with_aliases: iterable of (name, datatype, value, alias) tuples.
            ALL edge-level + device metrics for this edge appear here in alias order.
        seq: Sparkplug seq for this NBIRTH frame (resets the wraparound).
        bd_seq: current session generation for this edge.

    Returns: protobuf bytes ready to publish.

    The bdSeq metric is appended LAST per ADR-0007 convention.
    """
    ts = now_ms()
    metric_objs: list[Metric] = [
        Metric(timestamp=ts, name=name, datatype=dtype, value=value, alias=alias)
        for (name, dtype, value, alias) in metrics_with_aliases
    ]
    metric_objs.append(_build_bd_seq_metric(bd_seq, ts))
    return NBirth(timestamp=ts, seq=seq, metrics=tuple(metric_objs)).encode(include_dtypes=True)


def build_dbirth_payload(metrics_with_aliases: Iterable[tuple[str, DataType, object, int]],
                         seq: int) -> bytes:
    """Build DBIRTH bytes (no bdSeq metric — DBIRTH is per-device, edge owns bdSeq)."""
    ts = now_ms()
    metric_objs = tuple(
        Metric(timestamp=ts, name=name, datatype=dtype, value=value, alias=alias)
        for (name, dtype, value, alias) in metrics_with_aliases
    )
    return DBirth(timestamp=ts, seq=seq, metrics=metric_objs).encode(include_dtypes=True)


def build_ddeath_payload(seq: int) -> bytes:
    """Build DDEATH bytes per Sparkplug B v3.0.0 § 5.4.5.

    DDEATH carries:
      - `timestamp` — bridge clock at the death event.
      - `seq` — the edge's monotonic counter (devices share the edge's seq).
      - NO metrics tuple (empty payload).
      - NO bdSeq metric (DDEATH inherits edge session; only NBIRTH/NDEATH carry bdSeq per § 6.4.16).

    Used by ScenarioRunner to fire a per-device offline at cue
    `oven4_ddeath_at_sec` (CONTEXT 999.4 D-04).
    """
    ts = now_ms()
    return DDeath(timestamp=ts, seq=seq).encode(include_dtypes=False)


def build_ndata_payload(updates: Iterable[tuple[int, DataType, object]], seq: int) -> bytes:
    """Build NDATA bytes — alias-only references (no name/datatype on the wire).

    Args:
        updates: iterable of (alias, datatype, value) — datatype is required by
            the pysparkplug encoder even though it's not on the wire (encoder
            uses it to pick the value oneof field).
        seq: Sparkplug seq (0..255 wraparound, bumped per published frame).

    Returns: protobuf bytes (smaller than NBIRTH — no names, no dtypes on wire).
    """
    ts = now_ms()
    metric_objs = tuple(
        Metric(timestamp=ts, name=None, datatype=dtype, value=value, alias=alias)
        for (alias, dtype, value) in updates
    )
    return NData(timestamp=ts, seq=seq, metrics=metric_objs).encode(include_dtypes=False)


def build_ddata_payload(updates: Iterable[tuple[int, DataType, object]], seq: int) -> bytes:
    """Build DDATA bytes — same shape as NDATA but for device-level updates."""
    ts = now_ms()
    metric_objs = tuple(
        Metric(timestamp=ts, name=None, datatype=dtype, value=value, alias=alias)
        for (alias, dtype, value) in updates
    )
    return DData(timestamp=ts, seq=seq, metrics=metric_objs).encode(include_dtypes=False)
