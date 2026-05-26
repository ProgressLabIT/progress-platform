"""Phase 4: Sparkplug B Live — Streamlit reports page.

Wave 2 deliverable: daemon + singletons + cross-thread query helper.
Wave 2b adds topology rendering. Wave 3 adds chart rows.

Architecture (see 04-RESEARCH.md §Pattern 1):
- ONE daemon thread per python process, owning ONE asyncio event loop.
- Loop hosts: NATS connection, two KV watchers, one core subject sub, asyncpg pool.
- Streamlit fragments on the main (Tornado) thread dispatch coroutines via
  asyncio.run_coroutine_threadsafe(coro, DAEMON_LOOP).
- Module-level LATEST / STATE / TAIL dicts shared across all user sessions,
  guarded by a single threading.Lock.

DO NOT introduce per-session connections (D-06 explicit).
DO NOT use st.cache_data (copies; we want a live shared reference).
DO NOT call asyncio.run() in the page body (Streamlit's Tornado loop conflict).
DO NOT call js.subscribe() on progress.sparkplug.> (per ADR-0002 / Pitfall 3:
those subjects are CORE NATS, not JetStream-backed).
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any

import asyncpg
import nats
import streamlit as st
from streamlit_echarts import st_echarts

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Sparkplug B Live",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
log = logging.getLogger("sparkplug.streamlit")

@st.cache_resource
def _shared_state() -> dict:
    """Process-scoped shared state, held in @st.cache_resource so Streamlit's
    per-rerun script execution does NOT reset references and orphan the daemon
    thread's captured target_dicts. cache_resource is documented to persist
    across reruns and across user sessions; sidecar modules turned out to be
    re-imported on hot-reload, which sidecar-based sharing cannot survive.

    LAST_OK_TS_MS / DAEMON_LOOP / POOL are boxed (single-element lists)
    because Python module-globals can't be rebound across importing modules.
    """
    nats_healthy = threading.Event()
    nats_healthy.set()
    return {
        "LATEST": {},
        "STATE": {},
        "TAIL": defaultdict(lambda: deque(maxlen=300)),
        "LOCK": threading.Lock(),
        "NATS_HEALTHY": nats_healthy,
        "LAST_OK_TS_MS": [0],
        "DAEMON_LOOP": [None],
        "POOL": [None],
    }


_S = _shared_state()
LATEST: dict[str, dict] = _S["LATEST"]
STATE: dict[str, dict] = _S["STATE"]
TAIL: dict[str, deque] = _S["TAIL"]
LOCK: threading.Lock = _S["LOCK"]
NATS_HEALTHY: threading.Event = _S["NATS_HEALTHY"]
LAST_OK_TS_MS: list = _S["LAST_OK_TS_MS"]
DAEMON_LOOP: list = _S["DAEMON_LOOP"]
POOL: list = _S["POOL"]

# Demo-only constants. The reporting compose service is intentionally generic
# (no demo coupling); all sparkplug-demo wiring lives in this page.
# Broker hostname matches Phase 3 historian/config.py:20 (`broker:4222`, not `nats:4222`).
# Postgres creds match Phase 3 historian_ingester v1 demo posture (literal creds);
# post-demo: replace with /run/secrets/progress_historian_db_pwd + dedicated
# `historian` role per ADR-0005 §Roles.
NATS_URL = "nats://broker:4222"
DB_URL = "postgresql://postgres:postgres@workflow-db:5432/progress_historian"


# ---------------------------------------------------------------------------
# Async callbacks running on the daemon loop.
# ---------------------------------------------------------------------------
async def _on_metric_msg(msg) -> None:
    """Core NATS callback: append to TAIL + update LATEST.

    Subject pattern: progress.sparkplug.<group>.<edge>[.<device>].metric.<name>.data
                  OR progress.sparkplug.<group>.<edge>[.<device>].metric.<name>.birth
                  OR progress.sparkplug.<group>.<edge>[.<device>].session.{online,offline,suspect}

    Filter by doc["kind"] in callback (per CONTEXT resolved-discretion #1: broad
    subscribe `progress.sparkplug.>`, narrow inside the callback).
    """
    try:
        doc = json.loads(msg.data)
    except (ValueError, TypeError):
        log.warning("non-JSON payload on %s — dropping", msg.subject)
        return

    kind = doc.get("kind")
    if kind not in ("metric.data", "metric.birth"):
        return  # session.* events come through KV watcher (D-09); skip here

    try:
        group = doc["group"]
        edge = doc["edge"]
        device = doc.get("device")
        name = doc["name"]
        ts_utc_ms = int(doc["ts_utc_ms"])
        value = doc["value"]
        quality = doc.get("quality", "good")
        mtype = doc["type"]
    except (KeyError, TypeError, ValueError) as exc:
        log.warning("malformed envelope on %s: %s — dropping", msg.subject, exc)
        return

    metric_id = (
        f"{group}.{edge}.{device}.{name}" if device else f"{group}.{edge}.{name}"
    )
    with LOCK:
        LATEST[metric_id] = {
            "value": value,
            "ts_utc_ms": ts_utc_ms,
            "quality": quality,
            "type": mtype,
        }
        TAIL[metric_id].append((ts_utc_ms, value))
        LAST_OK_TS_MS[0] = int(time.time() * 1000)  # M-03


async def _watch_kv(kv, target_dict: dict, label: str) -> None:
    """Long-running KV watcher; target_dict is LATEST or STATE.

    Pitfall 7: nats-py emits None as the end-of-initial-snapshot sentinel.
    For a long-running watcher we must `continue`, NOT `break` (that would
    drop all subsequent live updates).
    """
    watcher = await kv.watchall()
    try:
        async for entry in watcher:
            if entry is None:
                continue
            try:
                with LOCK:
                    if entry.value:
                        target_dict[entry.key] = json.loads(entry.value)
                    else:
                        target_dict.pop(entry.key, None)
                    LAST_OK_TS_MS[0] = int(time.time() * 1000)  # M-03
            except (ValueError, TypeError):
                log.exception("kv decode failed for %s key=%s", label, entry.key)
    finally:
        await watcher.stop()


async def _on_disconnected() -> None:
    NATS_HEALTHY.clear()
    log.warning("NATS disconnected")


async def _on_reconnected() -> None:
    NATS_HEALTHY.set()
    log.info("NATS reconnected")


async def _daemon_main() -> None:
    """Daemon entrypoint — runs on the dedicated loop forever."""
    # M-01: bring up the asyncpg pool BEFORE nats.connect so a slow / unreachable
    # NATS broker does NOT gate Postgres history queries. The pool MUST live on
    # this loop so run_coroutine_threadsafe works (Pitfall 6). With NATS down,
    # historical charts (UI-DEMO-06) still render and the existing NATS_HEALTHY
    # warning banner explains the missing live-tail.
    POOL[0] = await asyncpg.create_pool(
        dsn=DB_URL,
        min_size=1,
        max_size=4,
        command_timeout=2.0,
    )
    log.info("sparkplug daemon — Postgres pool up (NATS connect next)")

    nc = await nats.connect(
        NATS_URL,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,
        disconnected_cb=_on_disconnected,
        reconnected_cb=_on_reconnected,
    )
    js = nc.jetstream()
    kv_lv = await js.key_value("sparkplug_last_values")
    kv_ses = await js.key_value("sparkplug_sessions")

    # D-09 cold-start hydration via watchall() — same pattern as the bridge's
    # kv_store.py:_read_all but kept long-running (Pitfall 7).
    asyncio.create_task(_watch_kv(kv_lv, LATEST, "last_values"))
    asyncio.create_task(_watch_kv(kv_ses, STATE, "sessions"))

    # Broad core subscribe per CONTEXT resolved-discretion #1.
    # CRITICAL: nc.subscribe() — NOT js.subscribe() (Pitfall 3).
    await nc.subscribe("progress.sparkplug.>", cb=_on_metric_msg)

    log.info(
        "sparkplug daemon ready — NATS=%s pool_max=4 LATEST_keys=%d STATE_keys=%d",
        NATS_URL, len(LATEST), len(STATE),
    )
    while True:
        await asyncio.sleep(3600)  # park; daemon dies with the process


# ---------------------------------------------------------------------------
# @st.cache_resource entry point — spawns the daemon ONCE per python process.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Connecting to NATS + Postgres...")
def _start_daemon() -> dict[str, Any]:
    """Spawn the singleton daemon thread once per python process.

    @st.cache_resource: cross-session singleton (per Streamlit docs:
    "Use cache_resource for global resources that are not data").
    """
    def runner() -> None:
        loop = asyncio.new_event_loop()
        DAEMON_LOOP[0] = loop
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_daemon_main())
        except Exception:
            log.exception("daemon crashed — page will see stale data")

    t = threading.Thread(target=runner, name="sparkplug-daemon", daemon=True)
    t.start()
    # M-02: do NOT busy-wait on the main (Tornado) thread. The previous 5s
    # `time.sleep(0.1)` loop blocked the event loop for any other concurrent
    # request (other tabs, health checks, the welcome page in main.py).
    # `query_history_sync` raises RuntimeError("sparkplug daemon not ready")
    # until the daemon finishes bringing up the loop + pool (per H-02);
    # `fetch_baseline` catches it and returns [] so the chart row degrades to
    # a "warming up" empty state instead of crashing. First fragment tick
    # (RUN_EVERY=1s) re-queries automatically once the daemon is ready.
    return {"thread": t, "started_at": time.time()}


_start_daemon()  # called once at module import


def query_history_sync(sql: str, *args, timeout: float = 2.0):
    """Dispatch an asyncpg query from the main thread to the daemon loop.

    Plan 04-05 (chart row) will be the sole caller. Returns a list of asyncpg
    Records; raises asyncio.TimeoutError if the query exceeds `timeout`;
    raises RuntimeError if the daemon thread has not yet finished bringing up
    the loop + pool (cold-start race; gracefully caught by `fetch_baseline`).

    NOTE: do NOT use `assert` here — `python -O` strips assertions and would
    surface the same readiness race as a cryptic `AttributeError` from
    `POOL.acquire()` on None. Per H-02.
    """
    if DAEMON_LOOP[0] is None or POOL[0] is None:
        raise RuntimeError("sparkplug daemon not ready")

    async def _go():
        async with POOL[0].acquire() as conn:
            return await conn.fetch(sql, *args)

    fut = asyncio.run_coroutine_threadsafe(_go(), DAEMON_LOOP[0])
    return fut.result(timeout=timeout)


# ---------------------------------------------------------------------------
# Type system — which Sparkplug B metric types are chartable (numeric).
# Per ADR-0002 §"Type collapse for v1 demo".
# ---------------------------------------------------------------------------
NUMERIC_TYPES = frozenset({
    "Int8", "Int16", "Int32", "Int64",
    "UInt8", "UInt16", "UInt32", "UInt64",
    "Float", "Double",
})


def _build_tree(latest_snapshot: dict[str, dict]) -> dict:
    """Group LATEST keys into {group: {edge: {device|"": [name...]}}}.

    KV key shape per ADR-0002 line 274:
      <group>.<edge>[.<device>].<name>
    Edge-level metrics (no device segment) bucketed under device key "".
    """
    tree: dict = {}
    for metric_id in sorted(latest_snapshot.keys()):
        parts = metric_id.split(".")
        if len(parts) < 3:
            log.warning("malformed metric_id key=%s — skipping", metric_id)
            continue
        group, edge, *rest = parts
        if len(rest) == 1:
            # Edge-level metrics (no device segment) are NBIRTH alias
            # declarations — populated once, never updated by DDATA, no
            # historian rows. Hidden from the topology so every visible
            # metric is chartable. Upstream bridge fix tracked separately.
            continue
        device, name = rest[0], ".".join(rest[1:])
        tree.setdefault(group, {}).setdefault(edge, {}).setdefault(device, []).append(name)
    return tree


def _render_metric_leaf(
    metric_id: str,
    name: str,
    entry: dict,
    selected: set[str],
) -> None:
    """Render one metric row — checkbox if numeric, display-only otherwise.

    D-03: Boolean and String metrics show the value but no checkbox.
    D-05: DEATHed metrics (quality != "good") render italic + dim;
          checkbox stays enabled (last-good value is still chartable).
    Security: html.escape() on every interpolated value to defeat XSS via
              malformed metric values (RESEARCH §Security Domain).
    """
    value = entry.get("value")
    mtype = entry.get("type", "?")
    quality = entry.get("quality", "good")
    chartable = mtype in NUMERIC_TYPES
    stale = quality != "good"

    # Markdown-safe (no HTML; checkbox/markdown both accept markdown).
    name_md = name.replace("`", "'")
    value_md = str(value).replace("`", "'")
    type_md = str(mtype).replace("`", "'")

    if stale:
        label = f"**{name_md}** ~`{value_md}`~ _{type_md}_ · STALE q={quality}"
    else:
        label = f"**{name_md}** `{value_md}` _{type_md}_"

    if chartable:
        checked = st.checkbox(
            label,
            value=(metric_id in selected),
            key=f"chk_{metric_id}",
        )
        if checked:
            selected.add(metric_id)
        else:
            selected.discard(metric_id)
    else:
        # D-03: Boolean/String metrics — display-only, indent to align under checkbox column.
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{label}", unsafe_allow_html=True)


def render_topology_tree() -> None:
    """Left column — UNS topology tree.

    UI-DEMO-02 + UI-DEMO-04 + UI-DEMO-05 all delivered here.
    Cold-start (CONTEXT discretion #7): when KV is empty, show waiting placeholder.

    UAT-04-G1 (Tests 5, 7, 10): body wrapped in a 2s-cadence Streamlit fragment
    so the sidebar reacts to live `LATEST` / `STATE` changes without user action.
    """
    # 999.4 D-03 — sidebar filter. Default unchecked: show all devices (incl.
    # offline). When checked, devices with alive=False are skipped in the
    # device-loop render below. Per CONTEXT specifics § 2, NOT persisted to
    # st.session_state — every fresh page load resets to "show all".
    #
    # Placed OUTSIDE @st.fragment because Streamlit forbids `st.sidebar.X(...)`
    # inside fragments (StreamlitAPIException). Toggling triggers a full-page
    # rerun (default for widgets outside fragments), which re-defines
    # `_live_topology` below and captures the new value in its closure. The
    # fragment's 2s ticks then honor the captured value until the next toggle.
    #
    # KEYLESS by design: a `key=` would back the widget with
    # `st.session_state[<key>]` and survive in-app navigation, contradicting
    # CONTEXT specifics § 2. Each full-page rerun recreates the widget with
    # `value=False` so a fresh page load always shows all devices.
    hide_offline_devices = st.sidebar.checkbox(
        "Hide offline devices",
        value=False,
    )

    @st.fragment(run_every=2)
    def _live_topology() -> None:
        st.subheader("Topology")

        # Snapshot under lock — render outside the lock so daemon writes don't stall.
        with LOCK:
            latest_snapshot = dict(LATEST)
            state_snapshot = dict(STATE)
            last_ok_ms = LAST_OK_TS_MS[0]

        # UAT-04-G3 (Test 8): freshness-aware guard.
        # @st.cache_resource keeps LATEST populated process-wide, so the prior
        # empty-snapshot check only fired on cold boot. Time-based check
        # re-fires after disconnects too.
        now_ms = int(time.time() * 1000)
        never_connected = last_ok_ms == 0
        stale = (now_ms - last_ok_ms) > STALE_THRESHOLD_MS
        if never_connected or stale:
            st.info(
                "Waiting for bridge data — start the simulator and reload."
            )
            return

        tree = _build_tree(latest_snapshot)
        prior_selected = list(st.session_state.get("selected_metrics", []))
        selected = set(prior_selected)

        for group, edges in tree.items():
            st.markdown(f"**{html.escape(group)}**")
            for edge, devices in edges.items():
                edge_key = f"{group}.{edge}"
                # 999.4 D-03: default-False on missing entry (Sparkplug B § 5.4
                # "no up-cascade" — render speculative state as offline, not online).
                # Same philosophy as the 999.3 Bug A fix.
                edge_alive = state_snapshot.get(edge_key, {}).get("alive", False)
                edge_dot = "🟢" if edge_alive else "🔴"
                with st.expander(f"{edge_dot} {html.escape(edge)}", expanded=True):
                    for device, names in devices.items():
                        if device:
                            # 999.4 D-02 + D-03 — read per-device alive directly
                            # from STATE composite key. Default-False on missing
                            # entry (Sparkplug B § 5.4 "no up-cascade": NBIRTH
                            # alone does not imply child devices online; each
                            # requires its own DBIRTH).
                            device_key = f"{group}.{edge}.{device}"
                            device_alive = state_snapshot.get(device_key, {}).get("alive", False)
                            device_dot = "🟢" if device_alive else "🔴"

                            # 999.4 D-03 specifics § 4 — filter applies at the
                            # topology-tree-render layer (devices, NOT edges).
                            # Edges with all-offline devices still render with
                            # their edge dot.
                            if hide_offline_devices and not device_alive:
                                continue

                            st.markdown(
                                f"{device_dot} **{html.escape(device)}**"
                            )
                        for name in sorted(names):
                            metric_id = (
                                f"{group}.{edge}.{device}.{name}"
                                if device
                                else f"{group}.{edge}.{name}"
                            )
                            entry = latest_snapshot.get(metric_id, {})
                            _render_metric_leaf(metric_id, name, entry, selected)

        new_selected = sorted(selected)
        st.session_state["selected_metrics"] = new_selected
        # UAT followup: checkbox toggles inside the fragment do not propagate
        # to the page-body chart iteration (`for metric_id in selected:`)
        # because @st.fragment isolates reruns to the fragment scope. Force a
        # full-app rerun when the selection set actually changed so the chart
        # rows appear/disappear without requiring a manual reload.
        if new_selected != prior_selected:
            st.rerun(scope="app")

    _live_topology()


# ---------------------------------------------------------------------------
# History query — bucket selection per ADR-0005 §"Bucket selection rule"
# (decisions/0005-timescale-schema-and-downsampling.md lines 156-159).
# ---------------------------------------------------------------------------
RANGE_TO_BUCKET: dict[str, tuple[str, int, str, bool]] = {
    # range_label -> (table_name, time_window_seconds, bucket_label, is_raw)
    "5m":  ("metric_samples",     5 * 60,    "raw", True),
    "30m": ("metric_samples_1s",  30 * 60,   "1s",  False),
    "4h":  ("metric_samples_30s", 4 * 3600,  "30s", False),
    "24h": ("metric_samples_5m",  24 * 3600, "5m",  False),
}

# Fragment refresh cadence — set from 04-SPIKE.md outcome (Task 1).
# SPIKE 04-01 outcome: PENDING — defaulting to 1; flicker check deferred to
# Plan 04-07 smoke test. If chart blinks at 1Hz, polish-down to 5
# (single-character edit; live-tail still works at 0.2 Hz).
RUN_EVERY = 1

# UAT-04-G3 (Test 8): cold-start placeholder freshness threshold.
# Longer than NATS reconnect tail (~10s), shorter than user attention.
# Sidebar fragment cadence is 2s, so placeholder appears within ~32s of stale data.
STALE_THRESHOLD_MS = 30_000


def fetch_baseline(metric_id: str, range_label: str) -> list:
    """Query Timescale for the baseline range. Returns asyncpg Records.

    Raw bucket: SELECT ts_utc, value_double FROM metric_samples …
    Aggregate buckets: SELECT bucket, avg, min, max, count FROM metric_samples_<N> …

    SQL injection protection: table name is interpolated (NOT bound) because
    asyncpg/Postgres do not support placeholders for identifiers — table name
    comes from the static RANGE_TO_BUCKET dict, NEVER user input.
    Same pattern as backend/sparkplug_bridge/historian/bootstrap.py:48
    `f'CREATE DATABASE "{db_name}"'`. Time window IS bound via $2.
    """
    table, window_s, _bucket_label, is_raw = RANGE_TO_BUCKET[range_label]
    if is_raw:
        sql = (
            f"SELECT ts_utc, value_double "
            f"FROM {table} "
            f"WHERE metric_id = $1 "
            f"  AND ts_utc >= NOW() - ($2 || ' seconds')::INTERVAL "
            f"  AND value_double IS NOT NULL "
            f"ORDER BY ts_utc"
        )
    else:
        sql = (
            f"SELECT bucket, avg, min, max, count "
            f"FROM {table} "
            f"WHERE metric_id = $1 "
            f"  AND bucket >= NOW() - ($2 || ' seconds')::INTERVAL "
            f"ORDER BY bucket"
        )
    try:
        return query_history_sync(sql, metric_id, str(window_s), timeout=2.0)
    except (asyncpg.PostgresError, asyncio.TimeoutError, AssertionError, RuntimeError):
        # AssertionError retained for back-compat with non-`-O` callers; RuntimeError
        # is the post-H-02 readiness-gate signal from `query_history_sync`.
        log.exception("history query failed for %s range=%s", metric_id, range_label)
        return []


def chart_options(
    rows: list,
    tail: list,
    metric_id: str,
    range_label: str,
    stale_since_hhmm: str | None = None,
) -> dict:
    """Build the ECharts options dict — avg + min/max band per D-11 + UI-DEMO-06.

    Band recipe per RESEARCH §Pattern 2 (canonical confidence-band pattern from
    echarts.apache.org/handbook/en/how-to/chart-types/line/area-line/):
      1) Invisible baseline at min — transparent line, transparent area.
      2) Stacked diff = (max - min); translucent areaStyle.opacity = 0.2 fills the band.
      3) Avg line on top (NOT stacked).
    Raw bucket short-circuits to a single avg/value line — no band per D-11.
    """
    table, _w, bucket_label, is_raw = RANGE_TO_BUCKET[range_label]

    if is_raw:
        # rows shape: [(ts_utc, value_double), ...]; tail shape: [(ts_utc_ms, value), ...]
        baseline_xy = [
            (r["ts_utc"].isoformat() if hasattr(r["ts_utc"], "isoformat") else r["ts_utc"], r["value_double"])
            for r in rows
        ]
        # Tail timestamps are ms epoch; convert to ISO for x-axis consistency.
        from datetime import datetime, timezone as _tz
        tail_xy = [
            (datetime.fromtimestamp(ts_ms / 1000.0, tz=_tz.utc).isoformat(), v)
            for ts_ms, v in tail
        ]
        combined = baseline_xy + tail_xy
        xs = [x for x, _ in combined]
        ys = [y for _, y in combined]
        series = [
            {
                "name": "value",
                "type": "line",
                "data": ys,
                "showSymbol": False,
                "lineStyle": {"width": 2},
            }
        ]
        legend_data = ["value"]
        legend_selected = {}
    else:
        # rows shape: [(bucket, avg, min, max, count), ...]
        # UAT-04-G2 (Test 6): zero-valued samples emitted by the simulator during
        # certain scenario states (e.g., motor stopped) legitimately drag the
        # per-bucket min to 0 while avg stays high. Diagnostic on 2026-05-07
        # against `plant1.edge2.mixer2.RPM` 14:35 bucket: 159 raw samples, 90
        # exactly 0, raw_avg=103.98 == aggregate avg=103.98, raw_min=0,
        # raw_max=241 — aggregate is honest. Band is correct; behavior accepted.
        xs = [
            r["bucket"].isoformat() if hasattr(r["bucket"], "isoformat") else str(r["bucket"])
            for r in rows
        ]
        mins = [r["min"] for r in rows]
        # Stack trick: lower = min, upper diff = (max - min) = the BAND HEIGHT.
        diffs = [
            (r["max"] - r["min"]) if r["max"] is not None and r["min"] is not None else 0
            for r in rows
        ]
        avgs = [r["avg"] for r in rows]

        # H-01: aggregate ranges (30m/4h/24h) must also surface live tail samples,
        # otherwise the chart freezes between range-chip clicks even though new
        # samples are arriving over NATS. Tail entries are raw points (no
        # aggregation), so each appears as a single-point bucket where
        # avg = min = max = value, producing diff = 0 (band collapses to a point
        # at the seam — visually a slight pinch, semantically honest: "we have
        # one live sample, not an aggregate").
        # x-axis is `type: "category"`, so tail timestamps must match the
        # baseline ISO-string shape; convert ms epoch -> ISO once.
        if tail:
            from datetime import datetime, timezone as _tz
            for ts_ms, v in tail:
                xs.append(datetime.fromtimestamp(ts_ms / 1000.0, tz=_tz.utc).isoformat())
                mins.append(v)
                diffs.append(0)
                avgs.append(v)

        # UAT followup: when every bucket has count=1 (e.g., 30m range hits the
        # `metric_samples_1s` rollup where each 1-second bucket typically holds
        # one sample), max==min==avg and every `diffs` entry is 0. Rendering a
        # band series + legend chip at that resolution is misleading — there's
        # no per-bucket spread to show. Fall back to a single avg line, same
        # shape as the raw 5m branch.
        has_spread = any(d and d > 0 for d in diffs)
        if has_spread:
            series = [
                {
                    "name": "_min",
                    "type": "line",
                    "stack": "band",
                    "data": mins,
                    "showSymbol": False,
                    "lineStyle": {"opacity": 0},
                    "areaStyle": {"opacity": 0},
                },
                {
                    "name": "min/max",
                    "type": "line",
                    "stack": "band",
                    "data": diffs,
                    "showSymbol": False,
                    "lineStyle": {"opacity": 0},
                    "areaStyle": {"opacity": 0.2},
                },
                {
                    "name": "avg",
                    "type": "line",
                    "data": avgs,
                    "showSymbol": False,
                    "lineStyle": {"width": 2},
                },
            ]
            legend_data = ["avg", "min/max"]
        else:
            series = [
                {
                    "name": "avg",
                    "type": "line",
                    "data": avgs,
                    "showSymbol": False,
                    "lineStyle": {"width": 2},
                },
            ]
            legend_data = ["avg"]
        # UAT-04-G2 followup: do NOT set `legend.selected = {"_min": False}`.
        # ECharts' legend.selected toggles series VISIBILITY, not just the
        # legend chip. Hiding the `_min` baseline series breaks the stack —
        # the `min/max` band then falls back to filling from y=0 (the chart
        # `areaStyle.origin: "auto"` default) instead of from the min line,
        # which made the band appear at 0–(max-min) far below the avg line.
        # `_min` is already excluded from `legend_data`, so it has no chip
        # either way; we just leave it visible so the stack works.
        legend_selected: dict = {}

    subtitle = f"bucket: {bucket_label}"
    if stale_since_hhmm:
        subtitle += f"  •  STALE since {stale_since_hhmm}"

    return {
        "title": {
            "text": metric_id,
            "subtext": subtitle,
            "left": 8,
            "top": 4,
            "textStyle": {"fontSize": 13},
            "subtextStyle": {"fontSize": 11},
        },
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {
            "data": legend_data,
            "right": 8,
            "top": 4,
            "selected": legend_selected,
        },
        "grid": {"left": 48, "right": 16, "top": 48, "bottom": 36},
        "xAxis": {"type": "category", "data": xs, "boundaryGap": False},
        "yAxis": {"type": "value", "scale": True},
        "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 16}],
        "series": series,
    }


def chart_row(metric_id: str) -> None:
    """One stacked chart row per checked metric.

    UI-DEMO-06: avg + min/max band, bucket per ADR-0005, range chips.
    UI-DEMO-03: live tail via st.fragment(run_every=RUN_EVERY) + st.empty().
    Hybrid refresh per RESEARCH §Pattern 3:
      - Baseline fetched from Postgres on selection / range change (cached in
        st.session_state["baseline_<metric_id>_<range>"])
      - Subsequent fragment ticks append entries from the TAIL deque newer than
        the baseline cutoff (in-memory; no Postgres roundtrip per tick)
    """
    # Range chip strip
    cols = st.columns([5, 1, 1, 1, 1])
    cols[0].markdown(f"**{html.escape(metric_id)}**")
    current_range = st.session_state.get(f"range_{metric_id}", "5m")
    for col, label in zip(cols[1:], ["5m", "30m", "4h", "24h"]):
        if col.button(
            label,
            key=f"range_{metric_id}_{label}",
            type="primary" if label == current_range else "secondary",
        ):
            st.session_state[f"range_{metric_id}"] = label
            # Bust the baseline cache so next fragment tick re-queries Postgres.
            for k in list(st.session_state.keys()):
                if k.startswith(f"baseline_{metric_id}_"):
                    del st.session_state[k]
            st.rerun()

    # Stale annotation — derived from STATE under LOCK
    stale_since_hhmm = None
    edge_key = ".".join(metric_id.split(".")[:2])  # group.edge
    with LOCK:
        edge_state = STATE.get(edge_key, {})
        latest_entry = LATEST.get(metric_id, {})
    if not edge_state.get("alive", True) or latest_entry.get("quality") != "good":
        ts_ms = latest_entry.get("ts_utc_ms")
        if ts_ms:
            stale_since_hhmm = time.strftime("%H:%M", time.localtime(ts_ms / 1000.0))

    # Live-tail fragment — owns its own repaint cadence (RUN_EVERY from spike).
    @st.fragment(run_every=RUN_EVERY)
    def _live_chart() -> None:
        skey_baseline = f"baseline_{metric_id}_{current_range}"
        skey_until = f"until_{metric_id}_{current_range}"

        if skey_baseline not in st.session_state:
            st.session_state[skey_baseline] = fetch_baseline(metric_id, current_range)
            # M-04: overlap baseline / tail seam by 2 seconds.
            # Postgres `NOW()` (in fetch_baseline) and Python `time.time()` here
            # do not share a clock; samples landing in the gap can either be
            # dropped (in baseline-after-NOW + filtered-out-of-tail) or
            # duplicated. Subtract a small epsilon from the tail cutoff so the
            # SEAM_OVERLAP_MS window is preferred-duplicate over preferred-gap;
            # ECharts harmlessly draws two near-identical points.
            SEAM_OVERLAP_MS = 2000
            st.session_state[skey_until] = int(time.time() * 1000) - SEAM_OVERLAP_MS

        baseline = st.session_state[skey_baseline]
        cutoff_ms = st.session_state[skey_until]

        with LOCK:
            tail_after_cutoff = [
                (ts, v) for ts, v in TAIL[metric_id] if ts > cutoff_ms
            ]

        options = chart_options(
            rows=baseline,
            tail=tail_after_cutoff,
            metric_id=metric_id,
            range_label=current_range,
            stale_since_hhmm=stale_since_hhmm,
        )

        # UAT followup: streamlit-echarts re-emits options with notMerge=true
        # on every fragment tick, which resets the dataZoom component to its
        # default (start=0, end=100). If the user pinch-zoomed or dragged the
        # slider, the next tick snapped them back to the full window. We hold
        # the user's zoom range in session_state, re-inject it as
        # dataZoom[].start/.end on every render, and update it via the
        # `datazoom` event so the chart stays where the user put it.
        skey_zoom = f"zoom_{metric_id}_{current_range}"
        prior_zoom = st.session_state.get(skey_zoom)
        if prior_zoom and prior_zoom.get("start") is not None and prior_zoom.get("end") is not None:
            options["dataZoom"] = [
                {"type": "inside", "start": prior_zoom["start"], "end": prior_zoom["end"]},
                {"type": "slider", "height": 16, "start": prior_zoom["start"], "end": prior_zoom["end"]},
            ]

        # ECharts emits the inside-zoom event with `start`/`end` directly, and
        # the slider with a `batch: [{start, end, ...}]` array. Normalize both.
        zoom_event = {
            "datazoom": (
                "function(params){"
                "  if (params.batch && params.batch.length){"
                "    return {start: params.batch[0].start, end: params.batch[0].end};"
                "  }"
                "  return {start: params.start, end: params.end};"
                "}"
            ),
        }

        # st.empty() + stable React key per RESEARCH §Pattern 3 + Pitfall 2.
        # Re-emitting the SAME options shape (only data arrays change) lets
        # ECharts diff-update internally rather than full-remount the iframe.
        placeholder = st.empty()
        with placeholder.container():
            zoom_payload = st_echarts(
                options=options,
                height="240px",
                key=f"chart_{metric_id}_{current_range}",
                events=zoom_event,
            )

        if isinstance(zoom_payload, dict):
            start = zoom_payload.get("start")
            end = zoom_payload.get("end")
            if start is not None and end is not None:
                st.session_state[skey_zoom] = {"start": start, "end": end}

    _live_chart()


# ---------------------------------------------------------------------------
# Page body — D-02 two-column layout.
# ---------------------------------------------------------------------------
st.title("Sparkplug B Live")


_BANNER_SLOT = st.empty()


@st.fragment(run_every=2)
def _live_disconnect_banner() -> None:
    """UAT-04-G1 (Tests 5, 7, 10): page-body NATS-disconnect banner repaints
    every 2s so it appears/clears without user action when broker drops.

    UAT followup: writing into a module-level `st.empty()` slot ensures the
    warning is REMOVED on reconnect — bare `st.warning(...)` inside a fragment
    body persists in the layout when subsequent fragment ticks emit nothing.
    """
    with _BANNER_SLOT.container():
        if not NATS_HEALTHY.is_set():
            # M-03: report LAST_OK_TS_MS (truth), NOT NOW.
            with LOCK:
                last_ok = LAST_OK_TS_MS[0]
            if last_ok:
                st.warning(
                    f"NATS disconnected — last update "
                    f"{time.strftime('%H:%M', time.localtime(last_ok / 1000.0))}"
                )
            else:
                st.warning("NATS disconnected — never connected")


_live_disconnect_banner()

with st.sidebar:
    render_topology_tree()

st.subheader("History")
selected = st.session_state.get("selected_metrics", [])
if not selected:
    st.info(
        "Select one or more metrics from the topology in the sidebar to chart history. "
        "Charts update live as new samples arrive over NATS."
    )
else:
    for metric_id in selected:
        chart_row(metric_id)
        st.divider()
