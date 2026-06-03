"""ADR-0002 envelope construction + NATS publish helpers.

Subject template (per km/decisions/0002-nats-subject-taxonomy.md):

  Edge-level NBIRTH:    progress.sparkplug.<group>.<edge>.session.online
  Device-level DBIRTH:  progress.sparkplug.<group>.<edge>.<device>.session.online
  Edge-level NDEATH:    progress.sparkplug.<group>.<edge>.session.offline
  Device-level DDEATH:  progress.sparkplug.<group>.<edge>.<device>.session.offline
  Edge metric birth:    progress.sparkplug.<group>.<edge>.metric.<name>.birth
  Edge metric data:     progress.sparkplug.<group>.<edge>.metric.<name>.data
  Device metric birth:  progress.sparkplug.<group>.<edge>.<device>.metric.<name>.birth
  Device metric data:   progress.sparkplug.<group>.<edge>.<device>.metric.<name>.data

NOTE on subject escapes: per ADR-0008, the bridge publishes plain NATS subjects
here — no `.` -> `//` escape applies on the Progress side. The escape rule only
affects raw bridged Sparkplug frames as seen from `nats sub spBv1//0.>`.
"""
import json
import logging
import re
import time

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

logger = logging.getLogger("sparkplug_bridge.publisher")

_SCHEMA_VERSION = 1

# Sparkplug group/edge/device tokens are slugified (lowercase, ASCII alphanum, dash) per ADR-0002.
_SLUG_RE = re.compile(r"[^a-z0-9-]+")


def slug(token: str) -> str:
    """Lowercase + ASCII-alphanumeric+dash slugification per ADR-0002.

    Input "Plant_1" -> "plant-1". Input "Edge.1" -> "edge-1".
    """
    return _SLUG_RE.sub("-", token.lower()).strip("-")


def build_envelope(
    group: str,
    edge: str,
    device: str | None,
    bd_seq: int,
    seq: int | None,
    source_ts_utc_ms: int | None,
) -> dict:
    """Build the ADR-0002 envelope. Caller adds kind-specific fields."""
    return {
        "schema_version": _SCHEMA_VERSION,
        "ts_utc_ms": int(time.time() * 1000),
        "source_ts_utc_ms": source_ts_utc_ms,
        "group": group,
        "edge": edge,
        "device": device,
        "bd_seq": bd_seq,
        "seq": seq,
    }


def build_session_subject(group: str, edge: str, device: str | None, online: bool) -> str:
    """Subject for NBIRTH/NDEATH (no device) or DBIRTH/DDEATH (with device)."""
    suffix = "session.online" if online else "session.offline"
    if device is None:
        return f"progress.sparkplug.{slug(group)}.{slug(edge)}.{suffix}"
    return f"progress.sparkplug.{slug(group)}.{slug(edge)}.{slug(device)}.{suffix}"


def build_metric_subject(group: str, edge: str, device: str | None, metric_name: str, kind: str) -> str:
    """Subject for per-metric publishes. `kind` MUST be 'data' or 'birth'."""
    if kind not in ("data", "birth"):
        raise ValueError(f"kind must be 'data' or 'birth', got {kind!r}")
    if device is None:
        return f"progress.sparkplug.{slug(group)}.{slug(edge)}.metric.{slug(metric_name)}.{kind}"
    return f"progress.sparkplug.{slug(group)}.{slug(edge)}.{slug(device)}.metric.{slug(metric_name)}.{kind}"


async def publish_session_online(group: str, edge: str, device: str | None, bd_seq: int, seq: int | None,
                                  source_ts_utc_ms: int | None, metrics: list[dict]) -> None:
    """Publish NBIRTH or DBIRTH (session.online) per ADR-0002."""
    subject = build_session_subject(group, edge, device, online=True)
    payload = build_envelope(group, edge, device, bd_seq, seq, source_ts_utc_ms)
    payload["kind"] = "session.online"
    payload["metrics"] = [
        {
            "name": m["name"],
            "alias": m["alias"],
            "type": m["datatype"],
            "value": m["value"],
            "quality": "good",
        }
        for m in metrics
    ]
    await nats_client.publish(subject, json.dumps(payload))


async def publish_session_offline(group: str, edge: str, device: str | None, bd_seq: int, seq: int | None,
                                   source_ts_utc_ms: int | None, reason: str) -> None:
    """Publish NDEATH or DDEATH (session.offline) per ADR-0002."""
    subject = build_session_subject(group, edge, device, online=False)
    payload = build_envelope(group, edge, device, bd_seq, seq, source_ts_utc_ms)
    payload["kind"] = "session.offline"
    payload["reason"] = reason
    await nats_client.publish(subject, json.dumps(payload))


async def publish_metric_birth(group: str, edge: str, device: str | None, bd_seq: int, seq: int | None,
                                source_ts_utc_ms: int | None, metric: dict) -> None:
    """Re-emit each NBIRTH/DBIRTH metric on its typed `metric.<name>.birth` subject (ADR-0002)."""
    subject = build_metric_subject(group, edge, device, metric["name"], "birth")
    payload = build_envelope(group, edge, device, bd_seq, seq, source_ts_utc_ms)
    payload.update({
        "kind": "metric.birth",
        "name": metric["name"],
        "alias": metric["alias"],
        "type": metric["datatype"],
        "value": metric["value"],
        "quality": "good",
    })
    await nats_client.publish(subject, json.dumps(payload))


async def publish_metric_data(
    group: str,
    edge: str,
    device: str | None,
    bd_seq: int,
    seq: int | None,
    source_ts_utc_ms: int | None,
    name: str,
    alias: int | None,
    datatype: str,
    value,
    *,
    quality: str = "good",
) -> None:
    """Publish NDATA/DDATA metric update on its typed `metric.<name>.data` subject (ADR-0002).

    Phase 2 adds the keyword-only `quality` parameter (default "good"). On
    NDEATH/DDEATH cascades (D-11), main.py calls publish_metric_stale (below)
    which delegates here with quality="stale". The enum is good|stale|bad
    per ADR-0002 § "Quality field".
    """
    if quality not in ("good", "stale", "bad"):
        raise ValueError(f"quality must be one of good/stale/bad, got {quality!r}")
    subject = build_metric_subject(group, edge, device, name, "data")
    payload = build_envelope(group, edge, device, bd_seq, seq, source_ts_utc_ms)
    payload.update({
        "kind": "metric.data",
        "name": name,
        "alias": alias,
        "type": datatype,
        "value": value,
        "quality": quality,
    })
    await nats_client.publish(subject, json.dumps(payload))


async def publish_metric_stale(
    group: str,
    edge: str,
    device: str | None,
    bd_seq: int,
    seq: int | None,
    source_ts_utc_ms: int | None,
    name: str,
    alias: int | None,
    datatype: str,
    last_value,
) -> None:
    """Re-publish a metric's last known value with quality="stale" (D-09 fan-out).

    Called from main.py's NDEATH/DDEATH cascade (Plan 02-06). UI consumers
    (Phase 4 UI-DEMO-04) interpret `quality="stale"` as visual de-emphasis
    without needing to derive staleness from BIRTH/DEATH events themselves.
    """
    await publish_metric_data(
        group, edge, device, bd_seq, seq, source_ts_utc_ms,
        name, alias, datatype, last_value,
        quality="stale",
    )


# The notification subject is FLAT — same destination as session.offline
# notifications go (the existing ServerEventManager fans this out via SSE).
# Distinct from the typed progress.sparkplug.<...>.session.* subjects.
_NOTIFICATION_SUBJECT = "progress.notification.sparkplug"


async def publish_session_suspect(
    group: str,
    edge: str,
    device: str | None,
    expected_seq: int,
    observed_seq: int,
    gaps_observed: int,
    gaps_window_sec: float,
    bd_seq: int,
) -> None:
    """Publish a session.suspect notification (D-06 + ADR-0002 amendment owed).

    Per CONTEXT.md <specifics> the envelope is flat (NOT the standard
    session envelope). Subject is the bridged notification subject so the
    existing ServerEventManager (subscribed to progress.notification.>)
    fans it out via SSE under topic name `sparkplug`.

    The `subject` field inside the payload identifies the affected session
    for downstream consumers; format mirrors ADR-0002's published
    progress.sparkplug.<group>.<edge>.session.online subject.
    """
    affected_session_subject = build_session_subject(group, edge, device, online=True)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "ts_utc_ms": int(time.time() * 1000),
        "kind": "session.suspect",
        "subject": affected_session_subject,
        "summary": f"seq gap on {edge}: expected {expected_seq}, observed {observed_seq}",
        "reason": "seq_gap",
        "payload_ref": {
            "group": group,
            "edge": edge,
            "device": device,
            "bd_seq": bd_seq,
            "expected_seq": expected_seq,
            "observed_seq": observed_seq,
            "gaps_observed": gaps_observed,
            "gaps_window_sec": gaps_window_sec,
        },
    }
    await nats_client.publish(_NOTIFICATION_SUBJECT, json.dumps(payload))
