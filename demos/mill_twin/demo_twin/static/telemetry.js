/**
 * telemetry.js — Wave 2 read path
 *
 * Responsibilities:
 *  - Connect to NATS over nats.ws (core subscribe, NOT JetStream)
 *  - Subscribe to progress.uns.plant1.area1.cell1.gantry1.*
 *  - Route each message by subject leaf to the right widget
 *  - Update watchlist rows (LAST / CHG / %CHG / SVG sparkline)
 *  - Update coolant tank bullet gauge
 *  - Update live state-distribution bars (D-19)
 *  - Drive the wall clock (setInterval)
 *  - Publish window.twinTelemetry + dispatch 'uns-sample' CustomEvents for 04-03
 *  - Forward chart leaves to charts.js via pushPoint()
 *
 * Threat mitigations:
 *  - T-04-05: every JSON.parse wrapped in try/catch; bad sample logged + skipped
 *  - T-04-06: all DOM writes use textContent / numeric formatting; no innerHTML of raw wire data
 */

import { connect, JSONCodec } from './vendor/nats.js';
import { pushPoint } from './charts.js';

// ─── Shared-state contract (consumed by 04-03 without touching this file) ────

window.twinTelemetry = {
  last: {},           // { [leaf]: value }
  lastFeedRate: 0,
  connState: 'connecting',
  snapTool: false,    // set by 04-03 on snap_tool fault; read by state-bar derivation
};

// ─── NATS config ──────────────────────────────────────────────────────────────

const NATS_WS_URL  = window.NATS_WS_URL  || 'ws://localhost:8090';
const SUBJECT      = 'progress.uns.plant1.area1.cell1.gantry1.*';
const RECONNECT_WAIT = 2000;

// ─── Per-leaf unit table (T-04-06: never echo raw unit strings into DOM) ──────

const UNIT_LABEL = {
  spindle_torque:   'N·m',
  spindle_power:    'kW',
  mrr:              'cm³/min',
  feed_rate:        'mm/min',
  spindle_load_pct: '%',
  spindle_temp:     '°C',
  coolant_flow:     'l/min',
  spindle_rpm:      'rpm',
  feed_per_tooth:   'mm/tooth',
  depth_of_cut:     'mm',
  tool_wear_pct:    '%',
  coolant_temp:     '°C',
};

// ─── Watchlist sparkline ring buffers ─────────────────────────────────────────

const SPARK_N = 20; // last 20 samples per leaf
const sparkBuffers = {}; // { [leaf]: number[] }

// ─── State-distribution derivation (D-19) ────────────────────────────────────
// Rolling counters over the last STATE_WINDOW ticks

const STATE_WINDOW = 150; // ~30 s at 5 Hz
const stateHistory = []; // ring of 'CUTTING'|'RAPID_POS'|'IDLE'|'ALARM' labels

// TOOL_CHANGE and PROBING stay at plausible constants (no live signal for them)
const STATE_FIXED = { TOOL_CHANGE: 6, PROBING: 5 };

// ─── Connection state management ─────────────────────────────────────────────

function setConnState(state) {
  window.twinTelemetry.connState = state;

  const dot   = document.getElementById('conn-dot');
  const label = document.getElementById('conn-label');
  const chip  = document.getElementById('run-chip');
  const chipDot   = document.getElementById('run-chip-dot');
  const chipLabel = document.getElementById('run-chip-label');

  if (!dot || !label || !chip) return;

  // Clear chip classes
  chip.classList.remove('connecting', 'live', 'reconnecting', 'stale');

  if (state === 'connecting') {
    // D-17: pre-telemetry
    dot.className = 'conn-dot grey';
    label.textContent = 'Connecting…';
    chip.classList.add('connecting');
    if (chipLabel) chipLabel.textContent = 'CONNECTING';
    setValuesGreyed(false);
    showDashes();
  } else if (state === 'live') {
    dot.className = 'conn-dot green';
    chip.classList.add('live');
    if (chipLabel) chipLabel.textContent = 'IN CYCLE';
    // RTT label refreshed separately
    refreshRttLabel();
    setValuesGreyed(false);
  } else if (state === 'reconnecting' || state === 'disconnected') {
    dot.className = 'conn-dot grey';
    label.textContent = 'Reconnecting…';
    chip.classList.add('reconnecting');
    if (chipLabel) chipLabel.textContent = 'STALE';
    setValuesGreyed(true);
  }
}

/** Show em-dash placeholders in watchlist LAST cells + coolant + chart badges */
function showDashes() {
  document.querySelectorAll('#watchlist-rows tr[data-leaf]:not([data-leaf="VIBRATION"]) .wl-last')
    .forEach(td => { td.textContent = '—'; });
  const cv = document.getElementById('coolant-value');
  if (cv) cv.textContent = '—';
  ['chart-power-val', 'chart-mrr-val', 'chart-torque-val'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = '—';
  });
}

/** Freeze + grey values (opacity 0.5) on reconnect; un-grey on live */
function setValuesGreyed(grey) {
  const opacity = grey ? '0.5' : '';
  document.querySelectorAll('.wl-last, .wl-spark, #coolant-value, #coolant-measure')
    .forEach(el => { el.style.opacity = opacity; });
  ['chart-power-val', 'chart-mrr-val', 'chart-torque-val'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.opacity = opacity;
  });
}

// Periodically refresh the RTT label when live
let rttInterval = null;
let _nc = null;

function refreshRttLabel(nc) {
  // nc may be passed on live-set; stored in module scope for interval
  if (nc) _nc = nc;
  const label = document.getElementById('conn-label');
  if (!label) return;
  if (!_nc) { label.textContent = 'LIVE · NATS'; return; }
  try {
    const rttPromise = _nc.rtt();
    if (rttPromise && typeof rttPromise.then === 'function') {
      rttPromise.then(rtt => {
        const ms = Math.round(Number(rtt) / 1_000_000); // nanos → ms
        label.textContent = `LIVE · NATS · ${ms}ms`;
      }).catch(() => {
        label.textContent = 'LIVE · NATS';
      });
    } else {
      label.textContent = 'LIVE · NATS';
    }
  } catch {
    label.textContent = 'LIVE · NATS';
  }
}

// ─── Signal router ────────────────────────────────────────────────────────────

/**
 * Route a decoded UNS sample to all relevant widgets.
 * Identity is the subject leaf ONLY — never read a name/metric field.
 */
function routeSignal(leaf, value, unit, ts) {
  // T-04-05: coerce to number; skip non-finite
  const v = Number(value);
  if (!Number.isFinite(v)) return;

  // Update shared state
  window.twinTelemetry.last[leaf] = v;
  if (leaf === 'feed_rate') window.twinTelemetry.lastFeedRate = v;

  // Dispatch for 04-03 (alarms, slider echo-confirm)
  window.dispatchEvent(new CustomEvent('uns-sample', { detail: { leaf, value: v, unit, ts } }));

  // Forward chart leaves
  if (leaf === 'spindle_power' || leaf === 'mrr' || leaf === 'spindle_torque') {
    pushPoint(leaf, v);
  }

  // Watchlist (skip VIBRATION — fixed constant D-07)
  if (leaf !== 'VIBRATION') {
    updateWatchlistRow(leaf, v);
  }

  // Coolant Tank bullet — reservoir level (drains), NOT the flow rate
  if (leaf === 'coolant_tank_pct') {
    updateCoolantBullet(v);
  }

  // State distribution (D-19) — needs torque + feed_rate
  if (leaf === 'spindle_torque' || leaf === 'feed_rate') {
    updateStateDistribution();
  }
}

// ─── Watchlist row updates ────────────────────────────────────────────────────

function formatValue(leaf, v) {
  // Format numeric value with appropriate precision; never echo raw unit from wire
  if (leaf === 'spindle_rpm') return v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v.toFixed(0);
  if (leaf === 'feed_rate') return v.toFixed(0);
  if (leaf === 'spindle_load_pct' || leaf === 'tool_wear_pct') return v.toFixed(1);
  if (leaf === 'coolant_flow') return v.toFixed(1);
  if (leaf === 'spindle_temp') return v.toFixed(1);
  if (leaf === 'spindle_power') return v.toFixed(1);
  if (leaf === 'spindle_torque') return v.toFixed(1);
  if (leaf === 'mrr') return v.toFixed(0);
  return v.toFixed(2);
}

function updateWatchlistRow(leaf, v) {
  const row = document.querySelector(`#watchlist-rows tr[data-leaf="${leaf}"]`);
  if (!row) return;

  const unit = UNIT_LABEL[leaf] || '';
  const display = `${formatValue(leaf, v)} ${unit}`.trim();

  // LAST cell
  const lastTd = row.querySelector('.wl-last');
  if (lastTd) lastTd.textContent = display;

  // Sparkline ring buffer
  if (!sparkBuffers[leaf]) sparkBuffers[leaf] = [];
  sparkBuffers[leaf].push(v);
  if (sparkBuffers[leaf].length > SPARK_N) sparkBuffers[leaf].shift();

  const sparkSvg = row.querySelector('.wl-sparkline');
  if (sparkSvg && sparkBuffers[leaf].length >= 2) {
    sparkSvg.setAttribute('points', buildSparklinePoints(sparkBuffers[leaf]));
  }
}

/** Build SVG polyline points string for a ring of values */
function buildSparklinePoints(values, w = 40, h = 18) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values.map((val, i) => {
    const x = (i / (values.length - 1)) * w;
    const y = h - ((val - min) / range) * (h - 2) - 1;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
}

// ─── Coolant Tank bullet gauge ────────────────────────────────────────────────

function updateCoolantBullet(v) {
  // Reservoir level, already a 0–100 %; clamp defensively.
  const pct = Math.max(0, Math.min(100, v));

  const valEl   = document.getElementById('coolant-value');
  const measure = document.getElementById('coolant-measure');

  if (valEl)   valEl.textContent = `${pct.toFixed(0)}%`;
  if (measure) measure.style.height = `${pct}%`;
  // #coolant-tick is a fixed reference line (seeded in HTML); it no longer
  // tracks the live value — the draining level falls past it.
}

// ─── State distribution bars (D-19) ──────────────────────────────────────────

function classifyState() {
  const torque   = window.twinTelemetry.last['spindle_torque'] ?? 0;
  const feedRate = window.twinTelemetry.last['feed_rate'] ?? 0;
  const snapActive = window.twinTelemetry.snapTool === true;

  if (snapActive) return 'ALARM';
  if (torque > 5 && feedRate > 0) return 'CUTTING';
  if (torque <= 5 && feedRate > 0) return 'RAPID_POS';
  return 'IDLE';
}

function updateStateDistribution() {
  const label = classifyState();
  stateHistory.push(label);
  if (stateHistory.length > STATE_WINDOW) stateHistory.shift();

  // Tally live buckets
  const counts = { CUTTING: 0, RAPID_POS: 0, IDLE: 0, ALARM: 0 };
  for (const s of stateHistory) counts[s] = (counts[s] || 0) + 1;
  const total = stateHistory.length;

  // Live percentages (floating; reserved 11% for TOOL_CHANGE + PROBING fixed)
  // Use "last bucket gets the remainder" to guarantee the four live buckets
  // sum to exactly (100 - reserved), preventing 99%/101% display artefacts (LR-03).
  const reserved = STATE_FIXED.TOOL_CHANGE + STATE_FIXED.PROBING;
  const livePool = 100 - reserved;
  const liveTotal = Math.max(1, total);
  const cutting   = Math.round((counts.CUTTING   / liveTotal) * livePool);
  const rapidPos  = Math.round((counts.RAPID_POS / liveTotal) * livePool);
  const alarm     = Math.round((counts.ALARM     / liveTotal) * livePool);
  const idle      = livePool - cutting - rapidPos - alarm; // absorbs rounding error
  const livePct = { CUTTING: cutting, RAPID_POS: rapidPos, IDLE: idle, ALARM: alarm };

  // Render each bar
  const bars = {
    CUTTING:     livePct.CUTTING,
    RAPID_POS:   livePct.RAPID_POS,
    TOOL_CHANGE: STATE_FIXED.TOOL_CHANGE,
    PROBING:     STATE_FIXED.PROBING,
    IDLE:        livePct.IDLE,
    ALARM:       livePct.ALARM,
  };

  for (const [state, pct] of Object.entries(bars)) {
    const row = document.querySelector(`[data-state="${state}"]`);
    if (!row) continue;
    const bar = row.querySelector('.state-bar');
    const val = row.querySelector('.state-val');
    if (bar) bar.style.width = `${pct}%`;
    if (val) val.textContent = `${pct}%`;
  }
}

// ─── Wall clock ───────────────────────────────────────────────────────────────

function tickClock() {
  const el = document.getElementById('clock-time');
  if (!el) return;
  const now = new Date();
  el.textContent = now.toLocaleTimeString('en-GB', { hour12: false });
}

// ─── NATS connect + retry loop ────────────────────────────────────────────────

const jc = JSONCodec();

/**
 * Attempt to connect to NATS once.
 * Returns the NatsConnection or throws on failure.
 */
async function tryConnect() {
  return await connect({
    servers:             [NATS_WS_URL],
    reconnect:           true,
    reconnectTimeWait:   RECONNECT_WAIT,
    reconnectJitter:     100,
    maxReconnectAttempts: -1,
  });
}

/**
 * Main entry point: connect (with retry on first-connect failure),
 * then subscribe and drain incoming messages.
 */
async function startTelemetry() {
  setConnState('connecting');

  // Retry loop for the initial connect (broker may not be up yet)
  let nc = null;
  while (!nc) {
    try {
      nc = await tryConnect();
    } catch (err) {
      console.warn('[telemetry] NATS initial connect failed, retrying in 2s:', err.message ?? err);
      setConnState('disconnected');
      await new Promise(r => setTimeout(r, RECONNECT_WAIT));
    }
  }

  _nc = nc;
  setConnState('live');
  refreshRttLabel(nc);

  // Periodic RTT refresh every 30 s
  if (rttInterval) clearInterval(rttInterval);
  rttInterval = setInterval(() => {
    if (window.twinTelemetry.connState === 'live') refreshRttLabel();
  }, 30_000);

  // Status watcher (concurrent — runs until nc is closed)
  (async () => {
    for await (const s of nc.status()) {
      if (s.type === 'disconnect' || s.type === 'reconnecting') {
        setConnState('reconnecting');
      } else if (s.type === 'reconnect') {
        setConnState('live');
        refreshRttLabel(nc);
      } else if (s.type === 'close') {
        setConnState('disconnected');
      }
      // 'error' and other types: log only
      if (s.type === 'error') {
        console.warn('[telemetry] NATS status error:', s.data ?? s);
      }
    }
  })();

  // Subscribe: exactly this subject with * at leaf position (Pitfall 4)
  const sub = nc.subscribe(SUBJECT);

  for await (const msg of sub) {
    try {
      const leaf = msg.subject.split('.').at(-1);
      // T-04-05: JSON.parse inside try; bad sample logged + skipped
      const env = jc.decode(msg.data); // {value, unit, source, ts}
      routeSignal(leaf, env.value, env.unit, env.ts);
    } catch (err) {
      console.warn('[telemetry] bad sample skipped:', err.message ?? err);
    }
  }
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Start wall clock immediately
  tickClock();
  setInterval(tickClock, 1000);

  // Render initial pre-telemetry state
  setConnState('connecting');

  // Start NATS — restart loop re-enters startTelemetry on permanent close (D-16)
  (async function boot() {
    while (true) {
      await startTelemetry().catch(err => {
        console.error('[telemetry] fatal, restarting in 5s:', err);
      });
      // startTelemetry only returns when the subscription iterator closes (permanent close)
      setConnState('reconnecting');
      await new Promise(r => setTimeout(r, 5000));
    }
  })();
});
