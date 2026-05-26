"""bdSeq + seq state-machine pure functions for the sparkplug bridge.

No async, no I/O, no module-level mutable state. The in-memory `sessions`
dict is owned by main.py (hydrated from sparkplug_sessions KV at startup);
these functions read and mutate it via parameter passing.

Per CONTEXT.md D-05/D-06/D-07/D-08 + RESEARCH §3:
  - bdSeq is 0-255 with valid wraparound 255 -> 0 (Sparkplug B v3.0.0)
  - seq is 0-255 with valid wraparound 255 -> 0 (per ADR-0002)
  - NDEATH whose bdSeq != current session bdSeq is dropped silently (D-05)
  - seq gap or alias miss increments gaps_observed; threshold trips suspect-cap (D-07)
  - Gap window is rolling: on each gap, if (now - window_start) > gap_window_sec,
    reset counter to 1 + bump window-start; else increment (CONTEXT.md <specifics>)
  - Suspect cap fires when gaps_observed >= gap_tolerance within the window
  - Counter resets to 0 on a clean NBIRTH (handled by reset_on_nbirth)
"""
import logging
import time
from typing import Optional

logger = logging.getLogger("sparkplug_bridge.session_state")

# The shape of one entry in the in-memory `sessions` dict.
# Mirrors the JSON written to sparkplug_sessions KV (kv_store.py SCHEMA_VERSION=1).
# Documented for callers; not enforced as a TypedDict to keep the dict mutable
# via assignment without ceremony.
#
# Per CONTEXT 999.4 D-01, the dict now holds BOTH edge-level entries
# (key "<group>.<edge>") AND device-level entries (key "<group>.<edge>.<device>");
# both share the same JSON shape. Device entries inherit `bd_seq` from the parent
# edge at write time (DBIRTH carries no bdSeq metric — Sparkplug B v3.0.0 § 6.4.16).
# Callers pass `device=None` (default) for edge sessions, `device="<id>"` for
# per-device sessions; the composite key disambiguates them in the same dict.
#
# {
#   "schema_version": 1,
#   "bd_seq": int,                       # 0-255, current session generation
#   "born_ts_utc_ms": int,               # bridge clock at NBIRTH ingest
#   "gaps_observed": int,                # counter inside rolling window
#   "gaps_window_started_ts_utc_ms": int, # window-start timestamp for rolling reset
#   "alive": bool,                       # False after NDEATH; True after NBIRTH
# }


def _now_ms() -> int:
    return int(time.time() * 1000)


def session_key(group: str, edge: str, *, device: Optional[str] = None) -> str:
    """Canonical sessions/last_seq KV key.

    Edge-only when ``device`` is None (returns ``"<group>.<edge>"``);
    composite ``"<group>.<edge>.<device>"`` when set. Per CONTEXT 999.4 D-01,
    the same in-memory ``_sessions`` dict and ``sparkplug_sessions`` KV bucket
    hold both edge-level and per-device entries — the composite key shape
    disambiguates them.
    """
    if device is None:
        return f"{group}.{edge}"
    return f"{group}.{edge}.{device}"


# ---- bdSeq predicates -----------------------------------------------------

def is_valid_nbirth_seq(last_bd_seq: Optional[int], new_bd_seq: int) -> bool:
    """Return True iff new_bd_seq is a valid successor to last_bd_seq.

    On fresh bridge start (no prior session), last_bd_seq is None and ANY
    new_bd_seq is accepted (RESEARCH §3 startup case).

    bdSeq wraps 255 -> 0 per Sparkplug B spec. The valid successor of
    last_bd_seq is `(last_bd_seq + 1) % 256`.
    """
    if last_bd_seq is None:
        return True
    return new_bd_seq == (last_bd_seq + 1) % 256


def is_stale_ndeath(session_bd_seq: int, ndeath_bd_seq: int) -> bool:
    """Return True if this NDEATH should be dropped silently (D-05).

    Per ADR-0002 § "Session and seq invariants": an NDEATH whose embedded
    bdSeq does NOT match the last NBIRTH's bdSeq is a stale LWT delivery
    (the broker held it from a previous session). Drop silently — do not
    publish session.offline.
    """
    return ndeath_bd_seq != session_bd_seq


# ---- seq predicates -------------------------------------------------------

def is_seq_gap(last_seq: int, new_seq: int) -> bool:
    """Return True if (last_seq, new_seq) represents a skipped frame (gap).

    seq wraps 255 -> 0; that transition is NORMAL, not a gap.
    Anything other than (last_seq + 1) % 256 is a gap.
    """
    if last_seq == 255 and new_seq == 0:
        return False
    return new_seq != (last_seq + 1) % 256


# ---- session-dict accessors -----------------------------------------------

def get_current_bd_seq(
    sessions: dict,
    group: str,
    edge: str,
    *, device: Optional[str] = None,
) -> Optional[int]:
    """Return the current bd_seq for the session, or None if no session yet.

    Edge-level when ``device`` is None; per-device when set (CONTEXT 999.4 D-01).
    """
    entry = sessions.get(session_key(group, edge, device=device))
    if entry is None:
        return None
    return entry.get("bd_seq")


def is_alive(
    sessions: dict,
    group: str,
    edge: str,
    *, device: Optional[str] = None,
) -> bool:
    """Return True if the session is currently alive.

    Edge-level when ``device`` is None; per-device when set (CONTEXT 999.4 D-01).
    """
    entry = sessions.get(session_key(group, edge, device=device))
    if entry is None:
        return False
    return bool(entry.get("alive", False))


# ---- gap-window state machine ---------------------------------------------

def record_gap(
    sessions: dict,
    group: str,
    edge: str,
    gap_tolerance: int,
    gap_window_sec: float,
    *, device: Optional[str] = None,
) -> bool:
    """Record one gap event and return True if the suspect cap is now reached.

    Edge-level when ``device`` is None; per-device when set (CONTEXT 999.4 D-01).

    Implements the rolling-window mechanic from CONTEXT.md <specifics>:
      - if no session entry exists, log and return False (caller should log
        & drop; no suspect cap can fire on a non-existent session)
      - else, if (now - gaps_window_started_ts_utc_ms) > gap_window_sec * 1000,
        reset gaps_observed to 1 and gaps_window_started_ts_utc_ms to now
      - else, increment gaps_observed
      - return True if gaps_observed >= gap_tolerance

    Caller (main.py) takes the boolean return and: if True, publishes
    session.offline with reason="bridge_timeout" + writes alive=False to KV.
    Counter does NOT reset here — it resets on the next clean NBIRTH (see
    reset_on_nbirth) or on the next out-of-window gap (above).
    """
    key = session_key(group, edge, device=device)
    entry = sessions.get(key)
    if entry is None:
        logger.warning(
            "record_gap: no session for %s — gap recorded but cannot fire suspect cap", key
        )
        return False

    now_ms = _now_ms()
    window_start = entry.get("gaps_window_started_ts_utc_ms", 0) or 0
    if (now_ms - window_start) > gap_window_sec * 1000:
        entry["gaps_observed"] = 1
        entry["gaps_window_started_ts_utc_ms"] = now_ms
    else:
        entry["gaps_observed"] = entry.get("gaps_observed", 0) + 1

    logger.info(
        "gap recorded: %s gaps_observed=%d tolerance=%d window_sec=%.1f",
        key,
        entry["gaps_observed"],
        gap_tolerance,
        gap_window_sec,
    )
    return entry["gaps_observed"] >= gap_tolerance


# ---- session lifecycle helpers --------------------------------------------

def start_session(
    sessions: dict,
    group: str,
    edge: str,
    bd_seq: int,
    *, device: Optional[str] = None,
) -> dict:
    """Create or replace the in-memory session entry.

    Edge-level when ``device`` is None (called on NBIRTH ingest); per-device
    when set (called on DBIRTH ingest, CONTEXT 999.4 D-01). Resets
    gaps_observed and gaps_window_started. Returns the new entry dict
    (caller writes it to KV via kv_store.encode_doc).
    """
    now_ms = _now_ms()
    entry = {
        "schema_version": 1,
        "bd_seq": bd_seq,
        "born_ts_utc_ms": now_ms,
        "gaps_observed": 0,
        "gaps_window_started_ts_utc_ms": now_ms,
        "alive": True,
    }
    sessions[session_key(group, edge, device=device)] = entry
    return entry


def mark_offline(
    sessions: dict,
    group: str,
    edge: str,
    *, device: Optional[str] = None,
) -> Optional[dict]:
    """Mark the session as offline (alive=False).

    Edge-level when ``device`` is None; per-device when set (CONTEXT 999.4 D-01).
    Returns the mutated entry dict (caller writes it to KV) or None if
    no session entry exists. Does NOT delete the entry — gaps_observed
    and bd_seq are preserved for diagnostic visibility.
    """
    key = session_key(group, edge, device=device)
    entry = sessions.get(key)
    if entry is None:
        return None
    entry["alive"] = False
    return entry


def reset_on_nbirth(
    sessions: dict,
    group: str,
    edge: str,
    *, device: Optional[str] = None,
) -> None:
    """Clear gaps_observed on a clean NBIRTH (D-07 recovery).

    Edge-level when ``device`` is None; per-device when set (CONTEXT 999.4 D-01).
    Called by main.py AFTER start_session has run. Idempotent.
    """
    entry = sessions.get(session_key(group, edge, device=device))
    if entry is None:
        return
    entry["gaps_observed"] = 0
    entry["gaps_window_started_ts_utc_ms"] = _now_ms()
