"""Sparkplug bridge service — asyncio entrypoint.

Phase 2 scope: full session-state-aware orchestration.
  - KV bootstrap (ensure_buckets) + cold-start hydration (_hydrate_caches)
  - bdSeq + seq state machine via session_state pure functions
  - Primary-host STATE handshake via host_state.handle_state_echo
  - NDEATH cascade ordering per D-11 (KV write → session.offline → stale fan-out)
  - D-12 device cascade synthesis on edge NDEATH
  - Bounded asyncio.Queue (depth 256, drop-oldest) per INGEST-07
  - Heartbeat enrichment via HostState

Phase 1 scope (D-05/D-06): subscribe to spBv1.0/# via aiomqtt; decode happy-path
NBIRTH/NDATA/NDEATH/DBIRTH/DDATA/DDEATH via vendored Eclipse Tahu; publish JSON
to progress.sparkplug.> per ADR-0002.
"""
import asyncio
import json
import logging
import os
import sys
from typing import Optional

import nats.errors
import nats.js.errors

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

from .config import get_config
from .decoder import (
    decode_payload,
    decode_sparkplug_topic,
    populate_aliases_from_birth,
    prune_aliases,
    resolve_alias,
)
from .heartbeat import heartbeat_loop
from .host_state import HostState, handle_state_echo
from .kv_store import (
    BUCKET_ALIASES,
    BUCKET_LAST_SEQ,
    BUCKET_LAST_VALUES,
    BUCKET_SESSIONS,
    encode_doc,
    ensure_buckets,
    hydrate_aliases,
    hydrate_last_seq,
    hydrate_last_values,
    hydrate_sessions,
)
from .publisher import (
    publish_metric_birth,
    publish_metric_data,
    publish_metric_stale,
    publish_session_offline,
    publish_session_online,
    publish_session_suspect,
)
from . import session_state
from .subscriber import run_subscribe_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("sparkplug_bridge")

# Sparkplug B `bdSeq` metric name — used to extract the session generation from
# NBIRTH / NDEATH frames. Per Sparkplug B v3.0.0 § 6.4.16.
_BD_SEQ_METRIC_NAME = "bdSeq"

# In-memory caches — single source of truth at runtime; KV is the persistent
# truth used for cold-start hydration after a bridge restart (RESEARCH §7).
# main.py owns these dicts; decoder/session_state functions take them as
# parameters so they remain pure-function modules.
_alias_cache: dict[tuple[str, str, int], dict[int, tuple[str, str]]] = {}
_sessions: dict[str, dict] = {}        # key: "<group>.<edge>" — see session_state.py docstring
_last_seq: dict[str, dict] = {}        # key: "<group>.<edge>" — value: {"seq": int, "ts_utc_ms": int}
_last_values: dict[str, dict] = {}     # key: "<group>.<edge>[.<device>].<name>"

# KV bucket handles populated by ensure_buckets() at startup.
_kv: dict = {}  # {BUCKET_*: KeyValue}

# The shared HostState instance — passed to subscriber.py and heartbeat_loop.
_state = HostState()

# INGEST-07 — bounded asyncio.Queue depth + drop-oldest policy.
_QUEUE_DEPTH = 256


def _extract_bd_seq(decoded: dict) -> Optional[int]:
    """Return the bdSeq value from a decoded NBIRTH/NDEATH metrics list, or None.

    Phase 1 returned 0 on absence (tolerance). Phase 2 returns None so the
    NBIRTH/NDEATH handler can reject malformed frames per ADR-0002.
    """
    for m in decoded.get("metrics", []):
        if m.get("name") == _BD_SEQ_METRIC_NAME:
            v = m.get("value")
            if v is not None:
                return int(v)
    return None


def _metric_value_id(group: str, edge: str, device: Optional[str], name: str) -> str:
    """Build the sparkplug_last_values KV key per CONTEXT.md <specifics>.

    Format: "<group>.<edge>" or "<group>.<edge>.<device>" + ".<name>"
    """
    if device is None:
        return f"{group}.{edge}.{name}"
    return f"{group}.{edge}.{device}.{name}"


# Sparkplug B v3.0.0 § 6.4.3 reserves these name prefixes for edge-scope
# metrics (e.g., NodeControl/Rebirth, NodeControl/Reboot, Properties/...).
# Device-scope user-defined metrics never use these prefixes per the spec —
# they appear only in NBIRTH, never DBIRTH. Used by Bug A fix (999.3-02) to
# distinguish edge-scope NBIRTH metrics that should seed `_last_values` at
# `<group>.<edge>.<name>` from device-scope NBIRTH metrics that DBIRTH will
# seed at `<group>.<edge>.<device>.<name>`.
_EDGE_SCOPE_NAME_PREFIXES = ("Node Control/", "NodeControl/", "Properties/")


def _is_edge_scope_metric_name(name: str) -> bool:
    """True if `name` belongs to a Sparkplug B reserved edge-scope namespace."""
    return any(name.startswith(p) for p in _EDGE_SCOPE_NAME_PREFIXES)


def _is_unknown_datatype(datatype: str) -> bool:
    """True if a decoded metric carries no on-wire datatype (alias-only frame).

    Per Sparkplug B v3.0.0 § 6.4.16, NDATA/DDATA payloads typically omit
    `datatype` (the BIRTH established it; subsequent frames just carry the
    alias + value). decoder.py renders an absent datatype as `Unknown(<n>)`.
    Used by the Bug B fix (999.3-02) to suppress the wire-vs-map datatype
    consistency check when the wire side has no datatype to compare.
    """
    return datatype.startswith("Unknown(")


async def handle_message(topic: str, payload: bytes) -> None:
    """Decode one Sparkplug frame and publish ADR-0002 envelopes per phase 2 rules."""
    parsed = decode_sparkplug_topic(topic)
    if parsed is None:
        return  # not Sparkplug

    if parsed["msg_type"] == "STATE":
        host_id = parsed.get("host_id") or ""
        cfg = get_config()
        handle_state_echo(_state, host_id, payload, expected_host_id=cfg.bridge_host_id)
        return

    decoded = decode_payload(payload)
    group = parsed["group"]
    edge = parsed["edge"]
    device = parsed["device"]
    msg_type = parsed["msg_type"]
    seq = decoded.get("seq")
    source_ts = decoded.get("timestamp")
    cfg = get_config()

    if msg_type == "NBIRTH":
        bd_seq = _extract_bd_seq(decoded)
        if bd_seq is None:
            logger.warning("NBIRTH without bdSeq metric — dropping (%s/%s)", group, edge)
            return

        # Validate bdSeq successor (255 -> 0 wraparound is normal).
        current = session_state.get_current_bd_seq(_sessions, group, edge)
        if not session_state.is_valid_nbirth_seq(current, bd_seq):
            # Out-of-sequence NBIRTH — accept but log; the simulator's mid-scenario
            # rebirth on edge2 is the canonical legitimate case.
            logger.info(
                "NBIRTH bdSeq jump for %s/%s: was=%s now=%d (accepting; rebirth)",
                group, edge, current, bd_seq,
            )

        # Bug B fix (999.3-02) — drop any in-queue NDATA/DDATA frames for this
        # (group, edge) BEFORE populating the new alias map. Sparkplug B
        # v3.0.0 § 6.4.16 specifies that NDATA/DDATA payloads do NOT carry
        # bdSeq, so the bridge cannot tell whether a queued data frame was
        # produced under the old session generation (with the prior alias
        # numbering) or under the new one. The simulator's
        # request_reorder_for_next_birth (simulator/main.py:145) makes alias
        # numbering shift across reconnects; resolving an old-session frame
        # against the new alias map silently lands the value on the wrong
        # (name, datatype) slot — the 999.2 UAT contamination signature.
        # Drain (drop) any queued NDATA/DDATA for this (group, edge) now;
        # legitimate post-NBIRTH data resumes on the simulator's next tick.
        dropped_count = _drain_data_for(_msg_queue, group, edge)
        if dropped_count > 0:
            logger.info(
                "NBIRTH for %s/%s: drained %d queued NDATA/DDATA frame(s) (cross-session safety)",
                group, edge, dropped_count,
            )

        # Update caches + KV.
        entry = session_state.start_session(_sessions, group, edge, bd_seq)
        session_state.reset_on_nbirth(_sessions, group, edge)
        populate_aliases_from_birth(_alias_cache, group, edge, bd_seq, decoded)

        await _kv[BUCKET_SESSIONS].put(
            session_state.session_key(group, edge), encode_doc(entry)
        )
        alias_doc = {
            "aliases": {
                str(m["alias"]): [m["name"], m["datatype"]]
                for m in decoded["metrics"]
                if m["alias"] is not None and m["name"] is not None
            }
        }
        await _kv[BUCKET_ALIASES].put(
            f"{group}.{edge}.{bd_seq}", encode_doc(alias_doc)
        )

        _state.active_session_count = sum(1 for s in _sessions.values() if s.get("alive"))

        # Seed sparkplug_last_seq so the FIRST NDATA after this NBIRTH can detect
        # a seq gap (D-06). Without seeding, _last_seq.get() returns None and the
        # gap-detection branch is skipped — silently breaking suspect emission.
        if seq is not None:
            seq_doc = {"seq": seq, "ts_utc_ms": (source_ts or 0)}
            _last_seq[session_state.session_key(group, edge)] = seq_doc
            await _kv[BUCKET_LAST_SEQ].put(
                session_state.session_key(group, edge), encode_doc(seq_doc)
            )

        await publish_session_online(
            group, edge, device, bd_seq, seq, source_ts, decoded["metrics"]
        )
        for m in decoded["metrics"]:
            if m["name"] is None or m["name"] == _BD_SEQ_METRIC_NAME:
                continue
            await publish_metric_birth(group, edge, device, bd_seq, seq, source_ts, m)
            # Seed sparkplug_last_values (D-10 cold-start hydration source).
            #
            # Bug A fix (999.3-02): The simulator's NBIRTH payload bundles edge-
            # level metrics AND every child device's metrics into one frame
            # (see simulator/scenario.py::_collect_all_metrics_for_birth). The
            # NBIRTH topic carries no device segment, so `device` is None here
            # for every metric in the loop. Writing device metrics under the
            # edge-scope vid `<group>.<edge>.<name>` produces persistent orphan
            # KV keys (Stratum B in 999.3-DIAGNOSIS.md) that never get cleaned
            # up — DBIRTH writes the correct device-scope vid alongside, and
            # neither the bridge nor the page consumer can distinguish the
            # orphan from a legitimate edge metric.
            #
            # Per Sparkplug B v3.0.0 § 6.4.3, only metrics in the reserved
            # edge-scope namespaces (`Node Control/...`, `NodeControl/...`,
            # `Properties/...`) live at edge scope; user-defined device
            # telemetry uses plain identifiers. We seed `_last_values` only
            # for edge-scope-reserved names and let DBIRTH (which carries the
            # device segment in its topic) seed device-scope state.
            if not _is_edge_scope_metric_name(m["name"]):
                continue
            vid = _metric_value_id(group, edge, device, m["name"])
            doc = {"value": m["value"], "type": m["datatype"], "ts_utc_ms": (source_ts or 0), "quality": "good"}
            _last_values[vid] = doc
            await _kv[BUCKET_LAST_VALUES].put(vid, encode_doc(doc))
        return

    elif msg_type == "DBIRTH":
        # Sparkplug B v3.0.0: DBIRTH carries no bdSeq metric — inherit edge session.
        bd_seq = session_state.get_current_bd_seq(_sessions, group, edge)
        if bd_seq is None:
            logger.warning(
                "DBIRTH before NBIRTH for %s/%s — dropping (no active edge session)",
                group, edge,
            )
            return

        # Extend alias cache + KV for this device's metrics. Per 02-01's kv_store
        # convention, callers use json.loads on raw entry.value (no decode_doc helper).
        populate_aliases_from_birth(_alias_cache, group, edge, bd_seq, decoded)

        # Per Sparkplug B v3.0.0 § 5.4.1 + CONTEXT 999.4 D-01: a device is
        # online only after its own DBIRTH. Track per-device alive state so
        # the page consumer can render device dots independently of edge dot
        # (no up-cascade). Inherit bd_seq from the parent edge — DBIRTH
        # carries no bdSeq metric (Sparkplug B v3.0.0 § 6.4.16).
        if device is not None:
            dev_entry = session_state.start_session(
                _sessions, group, edge, bd_seq, device=device,
            )
            await _kv[BUCKET_SESSIONS].put(
                session_state.session_key(group, edge, device=device),
                encode_doc(dev_entry),
            )
            _state.active_session_count = sum(
                1 for s in _sessions.values() if s.get("alive")
            )

        try:
            existing = await _kv[BUCKET_ALIASES].get(f"{group}.{edge}.{bd_seq}")
            existing_doc = json.loads(existing.value)
        except nats.js.errors.KeyNotFoundError:
            existing_doc = {"aliases": {}}
        for m in decoded["metrics"]:
            if m["alias"] is not None and m["name"] is not None:
                existing_doc["aliases"][str(m["alias"])] = [m["name"], m["datatype"]]
        await _kv[BUCKET_ALIASES].put(
            f"{group}.{edge}.{bd_seq}", encode_doc(existing_doc)
        )

        # Seed sparkplug_last_seq from DBIRTH seq for gap detection on subsequent
        # device-level DDATA frames (same key as edge — Sparkplug spec scopes seq
        # at the edge level, devices share the edge's seq counter).
        if seq is not None:
            seq_doc = {"seq": seq, "ts_utc_ms": (source_ts or 0)}
            _last_seq[session_state.session_key(group, edge)] = seq_doc
            await _kv[BUCKET_LAST_SEQ].put(
                session_state.session_key(group, edge), encode_doc(seq_doc)
            )

        await publish_session_online(
            group, edge, device, bd_seq, seq, source_ts, decoded["metrics"]
        )
        for m in decoded["metrics"]:
            if m["name"] is None:
                continue
            await publish_metric_birth(group, edge, device, bd_seq, seq, source_ts, m)
            vid = _metric_value_id(group, edge, device, m["name"])
            doc = {"value": m["value"], "type": m["datatype"], "ts_utc_ms": (source_ts or 0), "quality": "good"}
            _last_values[vid] = doc
            await _kv[BUCKET_LAST_VALUES].put(vid, encode_doc(doc))
        return

    elif msg_type == "NDEATH":
        ndeath_bd_seq = _extract_bd_seq(decoded)
        if ndeath_bd_seq is None:
            logger.warning("NDEATH without bdSeq metric — dropping (%s/%s)", group, edge)
            return

        session_bd_seq = session_state.get_current_bd_seq(_sessions, group, edge)
        if session_bd_seq is None:
            # No live session — could be a stale LWT from before bridge started.
            logger.info("NDEATH without prior session — dropping silently (%s/%s)", group, edge)
            return

        if session_state.is_stale_ndeath(session_bd_seq, ndeath_bd_seq):
            # D-05: drop silently, no session.offline emitted.
            logger.info(
                "stale NDEATH dropped: %s/%s session_bd_seq=%d ndeath_bd_seq=%d",
                group, edge, session_bd_seq, ndeath_bd_seq,
            )
            return

        await _ndeath_cascade(group, edge, device, msg_type, ndeath_bd_seq, seq, source_ts)
        return

    elif msg_type == "DDEATH":
        # Sparkplug B v3.0.0: DDEATH carries no bdSeq — inherit edge session.
        bd_seq = session_state.get_current_bd_seq(_sessions, group, edge)
        if bd_seq is None:
            logger.warning("DDEATH for unknown edge session %s/%s — dropping", group, edge)
            return

        await _ndeath_cascade(group, edge, device, msg_type, bd_seq, seq, source_ts)
        return

    if msg_type in ("NDATA", "DDATA"):
        bd_seq = session_state.get_current_bd_seq(_sessions, group, edge)
        if bd_seq is None:
            logger.warning("NDATA/DDATA before any (D)BIRTH for %s/%s — dropping", group, edge)
            return

        # seq monotonicity (D-06).
        last_doc = _last_seq.get(session_state.session_key(group, edge))
        if seq is not None and last_doc is not None:
            last_seq_val = last_doc.get("seq")
            if last_seq_val is not None and session_state.is_seq_gap(last_seq_val, seq):
                logger.warning(
                    "seq gap on %s/%s: expected %d observed %d",
                    group, edge, (last_seq_val + 1) % 256, seq,
                )
                cap_hit = session_state.record_gap(
                    _sessions, group, edge, cfg.gap_tolerance, cfg.gap_window_sec,
                )
                # Persist the updated session entry to KV so a bridge restart sees the counter.
                await _kv[BUCKET_SESSIONS].put(
                    session_state.session_key(group, edge),
                    encode_doc(_sessions[session_state.session_key(group, edge)]),
                )
                await publish_session_suspect(
                    group, edge, device,
                    expected_seq=(last_seq_val + 1) % 256,
                    observed_seq=seq,
                    gaps_observed=_sessions[session_state.session_key(group, edge)]["gaps_observed"],
                    gaps_window_sec=cfg.gap_window_sec,
                    bd_seq=bd_seq,
                )
                if cap_hit:
                    # D-07: bridge-induced offline.
                    await _bridge_timeout_offline(group, edge, device, bd_seq, seq, source_ts)
                    return  # do not publish further metric.data on a now-offline session

        # Update last_seq cache + KV.
        if seq is not None:
            seq_doc = {"seq": seq, "ts_utc_ms": (source_ts or 0)}
            _last_seq[session_state.session_key(group, edge)] = seq_doc
            await _kv[BUCKET_LAST_SEQ].put(
                session_state.session_key(group, edge), encode_doc(seq_doc)
            )

        for m in decoded["metrics"]:
            name = m["name"]
            datatype = m["datatype"]
            alias = m["alias"]
            if name is None and alias is not None:
                resolved = resolve_alias(_alias_cache, group, edge, bd_seq, alias)
                if resolved is None:
                    # D-08: alias miss counts toward gap budget.
                    logger.warning(
                        "alias %d unknown for %s/%s/bd_seq=%d — dropping + counting as gap",
                        alias, group, edge, bd_seq,
                    )
                    cap_hit = session_state.record_gap(
                        _sessions, group, edge, cfg.gap_tolerance, cfg.gap_window_sec,
                    )
                    await _kv[BUCKET_SESSIONS].put(
                        session_state.session_key(group, edge),
                        encode_doc(_sessions[session_state.session_key(group, edge)]),
                    )
                    if cap_hit:
                        await _bridge_timeout_offline(group, edge, device, bd_seq, seq, source_ts)
                        return
                    continue
                resolved_name, resolved_datatype = resolved
                # Bug B fix (999.3-02): Sparkplug B v3.0.0 § 6.4.16 specifies
                # that NDATA/DDATA payloads do NOT carry bdSeq, so the bridge
                # cannot identify which session generation produced the frame.
                # Combined with the simulator's `request_reorder_for_next_birth`
                # cue (simulator/main.py:145), an old-session DDATA buffered
                # across the reconnect would resolve its alias against the new
                # reordered alias map, land on the wrong (name, datatype) pair,
                # and write the old session's value into the wrong KV slot —
                # producing the 999.2 UAT contamination signature (see
                # 999.3-DIAGNOSIS.md § "Surface 3").
                #
                # The primary mitigation is the in-queue drain on NBIRTH
                # receipt (see _drain_data_for in handle_message NBIRTH branch).
                # This defensive check catches the residual case where a wire
                # frame DOES include a datatype (the simulator's
                # build_ndata_payload encodes datatypes optionally; the wire
                # may carry them on some edges/configurations or for diagnostic
                # echoes) and that wire datatype disagrees with the map. Only
                # fires for KNOWN wire datatypes; alias-only frames (the common
                # case where dtype field is omitted, decoded as `Unknown(0)`)
                # are NOT flagged here — they rely on the queue-drain.
                if not _is_unknown_datatype(datatype) and datatype != resolved_datatype:
                    logger.warning(
                        "alias %d datatype mismatch for %s/%s/bd_seq=%d — "
                        "wire=%s map=%s (stale cross-session frame) — dropping + counting as gap",
                        alias, group, edge, bd_seq, datatype, resolved_datatype,
                    )
                    cap_hit = session_state.record_gap(
                        _sessions, group, edge, cfg.gap_tolerance, cfg.gap_window_sec,
                    )
                    await _kv[BUCKET_SESSIONS].put(
                        session_state.session_key(group, edge),
                        encode_doc(_sessions[session_state.session_key(group, edge)]),
                    )
                    if cap_hit:
                        await _bridge_timeout_offline(group, edge, device, bd_seq, seq, source_ts)
                        return
                    continue
                name, datatype = resolved_name, resolved_datatype
            if name is None:
                continue
            await publish_metric_data(
                group, edge, device, bd_seq, seq, source_ts,
                name, alias, datatype, m["value"],
            )
            # Update sparkplug_last_values (D-10 KV+NATS coherence).
            vid = _metric_value_id(group, edge, device, name)
            doc = {"value": m["value"], "type": datatype, "ts_utc_ms": (source_ts or 0), "quality": "good"}
            _last_values[vid] = doc
            await _kv[BUCKET_LAST_VALUES].put(vid, encode_doc(doc))
        return

    logger.debug("unhandled msg_type=%s — dropped", msg_type)


async def _ndeath_cascade(
    group: str,
    edge: str,
    device: Optional[str],
    msg_type: str,
    bd_seq: int,
    seq: Optional[int],
    source_ts: Optional[int],
) -> None:
    """D-11 ordering: (1) KV write alive=False + last-values quality=stale,
    (2) publish session.offline (UI flips dot fastest),
    (3) iterate metrics + publish stale fan-out via asyncio.gather.

    For NDEATH (edge), also synthesizes per-device session.offline + stale
    fan-out per D-12 cascade.
    """
    # (1) Mark session offline in cache + KV. Scope by msg_type so that
    # NDEATH flips the EDGE session and DDEATH flips ONLY the device session
    # (Sparkplug B v3.0.0 § 5.4.5 — DDEATH leaves the edge online).
    target_device = device if msg_type == "DDEATH" else None
    entry = session_state.mark_offline(
        _sessions, group, edge, device=target_device,
    )
    if entry is None and target_device is not None:
        # No prior DBIRTH for this device — synthesize a minimal offline entry
        # so the KV row exists. Same pattern as the NDEATH per-device cascade
        # in Plan 01 (defensive: protocol allows DDEATH without preceding
        # DBIRTH on bridge restart edges; we want the KV truth either way).
        entry = {
            "schema_version": 1,
            "bd_seq": bd_seq,
            "born_ts_utc_ms": 0,
            "gaps_observed": 0,
            "gaps_window_started_ts_utc_ms": 0,
            "alive": False,
        }
        _sessions[session_state.session_key(group, edge, device=target_device)] = entry
    if entry is not None:
        await _kv[BUCKET_SESSIONS].put(
            session_state.session_key(group, edge, device=target_device),
            encode_doc(entry),
        )
    # Flip last_values quality to stale for affected metrics.
    affected_metric_ids = _affected_metric_ids(group, edge, device if msg_type == "DDEATH" else None)
    for vid in affected_metric_ids:
        doc = _last_values.get(vid)
        if doc is not None:
            doc["quality"] = "stale"
            await _kv[BUCKET_LAST_VALUES].put(vid, encode_doc(doc))

    # Prune alias map for the dying session and the matching KV key.
    # Sparkplug B v3.0.0 § 5.4.5: DDEATH leaves the edge online — pruning the
    # parent edge's alias map on DDEATH would starve subsequent NDATA/DDATA of
    # alias resolution and burn the gap budget into a bridge-induced offline.
    # Only NDEATH (edge death) ends the bdSeq generation that owns the aliases.
    if msg_type == "NDEATH":
        prune_aliases(_alias_cache, group, edge, bd_seq)
        try:
            await _kv[BUCKET_ALIASES].delete(f"{group}.{edge}.{bd_seq}")
        except Exception as e:  # noqa: BLE001
            logger.debug("alias KV delete benign error: %s", e)

    # (2) Publish session.offline for the dying entity.
    reason = "ndeath_lwt" if msg_type == "NDEATH" else "ddeath"
    await publish_session_offline(group, edge, device, bd_seq, seq, source_ts, reason)

    # (3) Stale fan-out (asyncio.gather — RESEARCH §4).
    stale_tasks = [
        _publish_stale_for_metric_id(vid, group, edge, bd_seq, seq, source_ts)
        for vid in affected_metric_ids
    ]

    if msg_type == "DDEATH":
        logger.info(
            "DDEATH cascade: device offline %s/%s/%s bd_seq=%d (edge stays online)",
            group, edge, device, bd_seq,
        )

    # D-12 + 999.4 D-02 — edge NDEATH cascades into per-device session.offline
    # AND persisted per-device KV rows. The KV write is the source of truth the
    # Streamlit page reads directly (no render-time inference per spec
    # § 5.4 "no up-cascade").
    if msg_type == "NDEATH":
        child_devices = _affected_devices_for_edge(group, edge)
        for child_device in child_devices:
            # (a) Update in-memory per-device session.
            dev_key = session_state.session_key(group, edge, device=child_device)
            dev_entry = session_state.mark_offline(
                _sessions, group, edge, device=child_device,
            )
            if dev_entry is None:
                # No prior DBIRTH observed for this device — synthesize a minimal
                # offline entry so the KV row exists (page reads default-False
                # on missing entry, but D-02 calls for explicit persisted truth).
                dev_entry = {
                    "schema_version": 1,
                    "bd_seq": bd_seq,
                    "born_ts_utc_ms": 0,
                    "gaps_observed": 0,
                    "gaps_window_started_ts_utc_ms": 0,
                    "alive": False,
                }
                _sessions[dev_key] = dev_entry
            # (b) Persist to sparkplug_sessions KV.
            await _kv[BUCKET_SESSIONS].put(dev_key, encode_doc(dev_entry))
            # (c) Synthetic NATS broadcast (preserved from D-12).
            stale_tasks.append(
                publish_session_offline(
                    group, edge, child_device, bd_seq, seq, source_ts,
                    "ndeath_cascade",
                )
            )

    if stale_tasks:
        await asyncio.gather(*stale_tasks, return_exceptions=True)

    _state.active_session_count = sum(1 for s in _sessions.values() if s.get("alive"))


async def _bridge_timeout_offline(
    group: str, edge: str, device: Optional[str], bd_seq: int,
    seq: Optional[int], source_ts: Optional[int],
) -> None:
    """D-07: bridge-induced offline when gap budget exhausted.

    Reuses _ndeath_cascade except reason='bridge_timeout' (already in
    ADR-0002's reason enum). Recovers on next clean NBIRTH (start_session
    + reset_on_nbirth).
    """
    entry = session_state.mark_offline(_sessions, group, edge)
    if entry is not None:
        await _kv[BUCKET_SESSIONS].put(
            session_state.session_key(group, edge), encode_doc(entry)
        )
    affected_metric_ids = _affected_metric_ids(group, edge, None)
    for vid in affected_metric_ids:
        doc = _last_values.get(vid)
        if doc is not None:
            doc["quality"] = "stale"
            await _kv[BUCKET_LAST_VALUES].put(vid, encode_doc(doc))
    await publish_session_offline(group, edge, device, bd_seq, seq, source_ts, "bridge_timeout")
    stale_tasks = [
        _publish_stale_for_metric_id(vid, group, edge, bd_seq, seq, source_ts)
        for vid in affected_metric_ids
    ]
    if stale_tasks:
        await asyncio.gather(*stale_tasks, return_exceptions=True)
    _state.active_session_count = sum(1 for s in _sessions.values() if s.get("alive"))


def _affected_metric_ids(group: str, edge: str, device: Optional[str]) -> list[str]:
    """Return metric_ids in _last_values that belong to (group, edge, [device]).

    For an NDEATH (device=None), returns ALL metric_ids under the edge
    (edge-scope + every child device). For a DDEATH, returns only the
    device-scope metrics.
    """
    if device is None:
        prefix_edge = f"{group}.{edge}."
        return [k for k in _last_values if k.startswith(prefix_edge)]
    prefix_dev = f"{group}.{edge}.{device}."
    return [k for k in _last_values if k.startswith(prefix_dev)]


def _affected_devices_for_edge(group: str, edge: str) -> list[str]:
    """Return distinct child device tokens from _last_values keys for this edge.

    Used by the D-12 NDEATH cascade to synthesize per-device session.offline
    events on edge death. Returns [] if no device-scope metrics are cached.

    Edge-scope metric names containing dots (e.g. `Properties/Schema.v1`,
    `NodeControl/Rebirth.Reason`) must NOT be misclassified as devices —
    Sparkplug B reserves dotted names in the `Properties/`, `Node Control/`,
    and `NodeControl/` namespaces. Gate via `_is_edge_scope_metric_name`
    before splitting on `.` (parallel guard to 999.3's contamination fix).
    """
    prefix = f"{group}.{edge}."
    devices: set[str] = set()
    for k in _last_values:
        if not k.startswith(prefix):
            continue
        tail = k[len(prefix):]
        if _is_edge_scope_metric_name(tail):
            # Edge-scope reserved namespace — never a device segment, even when
            # the name itself contains dots (e.g. `Properties/Schema.v1`).
            continue
        parts = tail.split(".", 1)
        # tail can be "<device>.<name>" (3+ tokens after the edge) or "<name>" (edge metric).
        # If parts has 2 elements, parts[0] is the device.
        if len(parts) == 2:
            devices.add(parts[0])
    return sorted(devices)


async def _publish_stale_for_metric_id(
    vid: str, group: str, edge: str, bd_seq: int,
    seq: Optional[int], source_ts: Optional[int],
) -> None:
    """Resolve metric_id back into (device, name, datatype, last_value) and publish stale."""
    doc = _last_values.get(vid)
    if doc is None:
        return
    # vid format: "<group>.<edge>.<name>" or "<group>.<edge>.<device>.<name>"
    # Strip the edge prefix; the remaining tail is either the edge-scope metric
    # name (which may itself contain dots, per Sparkplug B reserved namespaces
    # like `Properties/Schema.v1`) or "<device>.<name>". Gate via
    # `_is_edge_scope_metric_name` so dotted edge-scope names are not
    # misclassified as device-scope frames (parallel to the
    # `_affected_devices_for_edge` fix; both tripped the same naive split).
    prefix = f"{group}.{edge}."
    if not vid.startswith(prefix):
        return
    tail = vid[len(prefix):]
    if _is_edge_scope_metric_name(tail):
        device, name = None, tail
    else:
        parts = tail.split(".", 1)
        if len(parts) == 1:
            device, name = None, parts[0]
        else:
            device, name = parts[0], parts[1]
    await publish_metric_stale(
        group, edge, device, bd_seq, seq, source_ts,
        name, None, doc["type"], doc["value"],
    )


async def _hydrate_caches() -> None:
    """Cold-start hydration from KV (RESEARCH §7) — populates the four module caches."""
    _sessions.clear(); _sessions.update(await hydrate_sessions(_kv[BUCKET_SESSIONS]))
    _last_seq.clear(); _last_seq.update(await hydrate_last_seq(_kv[BUCKET_LAST_SEQ]))
    _last_values.clear(); _last_values.update(await hydrate_last_values(_kv[BUCKET_LAST_VALUES]))
    # Aliases: KV key is "<group>.<edge>.<bd_seq>" -> {aliases: {alias_int_str: [name, type]}}
    # Convert to in-memory shape (group, edge, bd_seq) -> {alias_int: (name, type)}.
    raw = await hydrate_aliases(_kv[BUCKET_ALIASES])
    _alias_cache.clear()
    for k, doc in raw.items():
        try:
            group_s, edge_s, bd_seq_s = k.rsplit(".", 2)
            bd_seq_n = int(bd_seq_s)
        except ValueError:
            logger.warning("alias KV key skipped (malformed): %s", k)
            continue
        mapping: dict[int, tuple[str, str]] = {}
        for alias_str, payload in (doc.get("aliases") or {}).items():
            try:
                mapping[int(alias_str)] = (payload[0], payload[1])
            except (ValueError, TypeError, IndexError):
                continue
        _alias_cache[(group_s, edge_s, bd_seq_n)] = mapping
    _state.active_session_count = sum(1 for s in _sessions.values() if s.get("alive"))
    logger.info(
        "hydration complete: sessions=%d aliases=%d last_seq=%d last_values=%d",
        len(_sessions), len(_alias_cache), len(_last_seq), len(_last_values),
    )


# Single-worker bounded queue. Drop-OLDEST policy on overflow per CONTEXT.md
# INGEST-07. Default depth 256 — abundant headroom for ADR-0007's ~50 msg/s
# peak (at queue depth full = ~5 seconds of buffered traffic).
_msg_queue: asyncio.Queue[tuple[str, bytes]] = asyncio.Queue(maxsize=_QUEUE_DEPTH)


async def _enqueue_message(topic: str, payload: bytes) -> None:
    """Subscriber callback — non-blocking enqueue with drop-oldest on full."""
    try:
        _msg_queue.put_nowait((topic, payload))
    except asyncio.QueueFull:
        # Drop the OLDEST item to make room (preserve recency).
        try:
            _msg_queue.get_nowait()
            _msg_queue.task_done()
        except asyncio.QueueEmpty:
            pass
        try:
            _msg_queue.put_nowait((topic, payload))
        except asyncio.QueueFull:
            logger.error("queue still full after drop-oldest — dropping new message")


def _drain_data_for(queue: "asyncio.Queue[tuple[str, bytes]]", group: str, edge: str) -> int:
    """Drop any queued NDATA/DDATA frame for (group, edge); preserve other items.

    Used by Bug B fix (999.3-02) to discard prior-session data frames that
    arrived before the new NBIRTH. Iterates through the queue in arrival
    order, requeuing every item that is NOT an NDATA/DDATA for the target
    (group, edge). The single-worker `_queue_worker` model means no other
    coroutine is consuming concurrently, so this drain is race-free.

    Returns the count of frames dropped.

    Topic matching uses string prefixes against the Sparkplug topic format
    `spBv1.0/<group>/NDATA/<edge>` and `spBv1.0/<group>/DDATA/<edge>/<dev>`
    (decode_sparkplug_topic). The slug forms are NOT substituted here —
    queue items hold the raw MQTT topic exactly as the broker delivered it.
    """
    target_ndata_prefix = f"spBv1.0/{group}/NDATA/{edge}"
    target_ddata_prefix = f"spBv1.0/{group}/DDATA/{edge}"
    dropped = 0
    keep: list[tuple[str, bytes]] = []
    while True:
        try:
            topic, payload = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        # Match: topic equals the prefix exactly OR prefix + '/' (DDATA has device suffix).
        if (
            topic == target_ndata_prefix
            or topic == target_ddata_prefix
            or topic.startswith(target_ndata_prefix + "/")
            or topic.startswith(target_ddata_prefix + "/")
        ):
            dropped += 1
            queue.task_done()  # drained items still need task_done() per asyncio.Queue contract
        else:
            keep.append((topic, payload))
            queue.task_done()
    # Re-enqueue the kept items in original order.
    for topic, payload in keep:
        try:
            queue.put_nowait((topic, payload))
        except asyncio.QueueFull:
            logger.error("queue full while requeuing during NBIRTH drain — dropping %s", topic)
    return dropped


async def _queue_worker() -> None:
    """Single worker that dequeues and dispatches to handle_message.

    Errors per-message are caught + logged so one bad frame never kills
    the loop (Phase 1 pattern preserved).
    """
    while True:
        topic, payload = await _msg_queue.get()
        try:
            await handle_message(topic, payload)
        except Exception:
            logger.exception("handle_message failed for %s", topic)
        finally:
            _msg_queue.task_done()


async def _wire_automations(cfg) -> "object | None":
    """Phase 5 — ADR-0010 pump-anomaly subscriber.

    Returns the NATS Subscription handle (for clean unsubscribe on shutdown)
    or None when the automation is disabled by env or the JWT file is missing.

    On FileNotFoundError, ONLY the automation is disabled — the bridge keeps
    running. RESEARCH §Pattern 2 + Open Question 1 recommend this graceful
    degradation: a missing JWT must not cascade to a bridge-wide outage.
    """
    if os.environ.get("SPARKPLUG_AUTOMATIONS_ENABLED", "true").lower() != "true":
        logger.info("automations disabled by SPARKPLUG_AUTOMATIONS_ENABLED=false")
        return None
    try:
        from .automations.pump_anomaly import PumpAnomalyAutomation
        automation = PumpAnomalyAutomation(
            api_base_url=cfg.api_base_url,
            token_path=cfg.sparkplug_token_path,
        )
    except FileNotFoundError as e:
        logger.error("automation token not readable, disabling: %s", e)
        return None

    async def _automation_cb(msg):
        try:
            payload = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        await automation.on_metric_data(payload)

    nc = nats_client.get_nats()
    sub = await nc.subscribe(
        "progress.sparkplug.plant1.edge1.pump3.metric.vibration.data",
        cb=_automation_cb,
    )
    logger.info(
        "PumpAnomalyAutomation subscribed (target=%s)",
        "plant1.edge1.pump3.Vibration",
    )
    return sub


async def main() -> None:
    cfg = get_config()
    logger.info(
        "sparkplug_bridge starting — NATS=%s MQTT=%s client_id=%s host_id=%s heartbeat=%.1fs",
        cfg.nats_url, cfg.mqtt_url, cfg.mqtt_client_id, cfg.bridge_host_id,
        cfg.bridge_heartbeat_interval_sec,
    )

    # 1. NATS first — JetStream context required for ensure_buckets.
    await nats_client.connect(cfg.nats_url)
    _state.nats_connected = True
    js = nats_client.get_nats().jetstream()

    # 2-3. KV ensure + hydrate.
    global _kv
    _kv = await ensure_buckets(js)
    await _hydrate_caches()

    # 4. Heartbeat task — published per interval; reads _state.
    hb_task = asyncio.create_task(
        heartbeat_loop("bridge", state=_state, interval_sec=cfg.bridge_heartbeat_interval_sec)
    )

    # 5. Queue worker — dispatches enqueued messages.
    worker_task = asyncio.create_task(_queue_worker())

    # 5b. Phase 5 (ADR-0010) — wire pump-anomaly automation if enabled.
    # Sits AFTER queue worker (5) and BEFORE MQTT subscribe loop (6) so the
    # NATS subscription is live before any decoded metric.data publish.
    auto_sub = await _wire_automations(cfg)

    try:
        # 6-9. MQTT subscribe loop — sets state.mqtt_connected, attaches LWT, subscribes
        # to STATE loopback + spBv1.0/#, publishes ONLINE retained, drains messages.
        # The subscriber's handle_message arg is _enqueue_message (drops-oldest under load).
        await run_subscribe_loop(cfg, _enqueue_message, _state)
    except asyncio.CancelledError:
        pass
    finally:
        if auto_sub is not None:
            try:
                await auto_sub.unsubscribe()
            except (nats.errors.Error, RuntimeError, asyncio.CancelledError):
                logger.exception("automation unsubscribe failed")
        for t in (worker_task, hb_task):
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass
        await nats_client.drain()
        logger.info("sparkplug_bridge stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
