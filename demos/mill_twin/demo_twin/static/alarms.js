/**
 * alarms.js — Wave 2 machine-side event/alarm log
 *
 * Responsibilities:
 *  - Seed #event-log-rows with 6 plausible machine-history rows on load (D-11)
 *  - Listen to window 'uns-sample' and evaluate Phase-3 thresholds (D-12):
 *      Overload: spindle_torque > 45.0 N·m sustained 25 consecutive ticks (5 s at 5 Hz)
 *      Breakage: spindle_torque < 5.0 N·m AND lastFeedRate > 0 (first tick, no dwell)
 *  - Export window.appendAlarm(severity, message, value) for controls.js button presses
 *  - Cap list at 200 rows; prepend new rows at top
 *
 * IMPORTANT (D-10): this is a MACHINE-SIDE log.
 *   It MUST NOT fetch or subscribe to any Progress alarm/work-record subject/REST endpoint.
 *   PANEL-06 is satisfied here — this log never mirrors server-side records.
 *
 * Threat mitigations:
 *  - T-04-11: all row text written via textContent only; no innerHTML of wire data
 */

// ─── Constants (Phase-3 thresholds — MUST match demos/mill_twin/mill_automation/config.py) ──

const TORQUE_LIMIT_NM    = 45.0;   // torque_limit_nm = 45.0
const OVERLOAD_TICKS     = 25;     // dwell_seconds=5.0 at 5 Hz → 25 consecutive ticks
const BREAKAGE_FLOOR_NM  = 5.0;    // breakage_floor_nm = 5.0
const MAX_ROWS           = 200;    // planner-discretion cap from 04-UI-SPEC

// ─── Severity color config (matches styles.css severity chips) ─────────────────

const SEVERITY_COLORS = {
  alarm: '#F0533B',
  warn:  '#F2B23E',
  info:  '#4A9FD8',
  ok:    '#35C98A',
};

// ─── Pre-seeded rows (D-11) ───────────────────────────────────────────────────
// Exact rows from 04-UI-SPEC §Event History / Alarm Log

const SEEDED_ROWS = [
  { time: '14:31:52', severity: 'alarm', message: 'Vibration over limit',    value: '4.6 mm/s'  },
  { time: '14:28:10', severity: 'warn',  message: 'Spindle temp rising',      value: '61 °C'     },
  { time: '14:22:45', severity: 'info',  message: 'Tool T-217 wear 62%',      value: '62 %'      },
  { time: '14:15:03', severity: 'info',  message: 'WCS G54 re-established',   value: 'OK'        },
  { time: '14:09:37', severity: 'warn',  message: 'Coolant flow dip detected', value: '31 L/min' },
  { time: '13:58:21', severity: 'info',  message: 'OP 040 roughing started',  value: 'O4408'     },
];

// ─── Row builder ─────────────────────────────────────────────────────────────

/**
 * Build a single event-row div with textContent-only writes (T-04-11).
 * @param {string} time     - HH:MM:SS formatted string
 * @param {string} severity - 'alarm' | 'warn' | 'info'
 * @param {string} message  - human-readable event description
 * @param {string|number} value - numeric + unit or 'OK'
 * @returns {HTMLDivElement}
 */
function buildRow(time, severity, message, value) {
  const row = document.createElement('div');
  row.className = 'event-row';

  const timeEl = document.createElement('span');
  timeEl.className = 'event-time';
  timeEl.textContent = time;

  const sevEl = document.createElement('span');
  sevEl.className = `severity-tag ${severity}`;
  sevEl.textContent = severity.toUpperCase();

  const msgEl = document.createElement('span');
  msgEl.className = 'event-message';
  msgEl.textContent = message;

  const valEl = document.createElement('span');
  // Use severity color class for value; if value is 'OK' use ok class
  const valClass = value === 'OK' ? 'ok' : severity;
  valEl.className = `event-value ${valClass}`;
  valEl.textContent = String(value);

  row.appendChild(timeEl);
  row.appendChild(sevEl);
  row.appendChild(msgEl);
  row.appendChild(valEl);

  return row;
}

// ─── Row container ────────────────────────────────────────────────────────────

function getLogContainer() {
  return document.getElementById('event-log-rows');
}

// ─── Seed rows on load ────────────────────────────────────────────────────────

function seedRows() {
  const container = getLogContainer();
  if (!container) return;

  // Clear any existing static rows (index.html has them as pre-seed; we manage dynamically)
  // Actually, index.html already has the seeded rows as static HTML (04-01 artifact).
  // alarms.js owns #event-log-rows after DOMContentLoaded — we leave those static rows
  // and only prepend live rows above them. The static rows ARE the seed (D-11 satisfied by markup).
  // However per the plan "render the six pre-seeded rows into #event-log-rows on load" — since
  // index.html already has them (frozen DOM from 04-01), we do not double-seed.
  // The static markup rows remain; alarms.js prepends live rows above them.
  // This is correct and avoids duplicate rows.
}

// ─── appendAlarm (exported on window) ─────────────────────────────────────────

/**
 * Prepend a new alarm row to #event-log-rows.
 * Called by controls.js for button presses; also called internally for threshold events.
 * @param {string} severity  - 'alarm' | 'warn' | 'info'
 * @param {string} message   - event description (textContent — safe)
 * @param {string|number} value - numeric value or ''
 */
window.appendAlarm = function appendAlarm(severity, message, value) {
  const container = getLogContainer();
  if (!container) return;

  const now = new Date();
  const time = now.toLocaleTimeString('en-GB', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const row = buildRow(time, severity, message, value === '' || value === undefined ? '' : String(value));
  container.insertBefore(row, container.firstChild);

  // Cap at MAX_ROWS (drop oldest from the bottom)
  const rows = container.querySelectorAll('.event-row');
  if (rows.length > MAX_ROWS) {
    for (let i = MAX_ROWS; i < rows.length; i++) {
      rows[i].remove();
    }
  }
};

// ─── Threshold state ──────────────────────────────────────────────────────────

// Overload (dwell) state
let overloadConsecutiveTicks = 0;
let overloadLatched = false;     // prevent repeat fire during same sustained excursion
let overloadClearTicks = 0;      // dwell below limit before re-arming (hysteresis)
const OVERLOAD_CLEAR_TICKS = 5;  // 5 ticks = 1 s clear before latch re-arms

// Breakage (no dwell) state
let breakageLatched = false;     // latch while condition holds; re-arm when condition clears

// ─── uns-sample listener ──────────────────────────────────────────────────────

/**
 * Evaluate Phase-3 alarm thresholds on every spindle_torque sample.
 * feed_rate is tracked via window.twinTelemetry.lastFeedRate (set by telemetry.js).
 */
window.addEventListener('uns-sample', (e) => {
  const { leaf, value } = e.detail;
  if (typeof value !== 'number' || !Number.isFinite(value)) return;

  if (leaf === 'spindle_torque') {
    const torque = value;
    const lastFeedRate = (window.twinTelemetry && window.twinTelemetry.lastFeedRate) || 0;

    // ── Overload detection (dwell = 25 ticks at 5 Hz = 5.0 s) ──────────────
    if (torque > TORQUE_LIMIT_NM) {
      overloadConsecutiveTicks++;
      overloadClearTicks = 0; // reset clear-dwell whenever torque is above limit
      if (overloadConsecutiveTicks >= OVERLOAD_TICKS && !overloadLatched) {
        overloadLatched = true;
        window.appendAlarm('alarm', 'Spindle torque overload', `${torque.toFixed(1)} N·m`);
      }
    } else {
      // Torque dropped to/below limit — reset exceedance counter immediately.
      // Re-arm the latch only after OVERLOAD_CLEAR_TICKS consecutive clear ticks
      // to prevent alarm spam from oscillation near the threshold.
      overloadConsecutiveTicks = 0;
      if (overloadLatched) {
        overloadClearTicks++;
        if (overloadClearTicks >= OVERLOAD_CLEAR_TICKS) {
          overloadLatched = false;
          overloadClearTicks = 0;
        }
      }
    }

    // ── Breakage detection (first tick, no dwell) ───────────────────────────
    // Condition: spindle_torque < 5.0 AND feed_rate > 0
    if (torque < BREAKAGE_FLOOR_NM && lastFeedRate > 0) {
      if (!breakageLatched) {
        breakageLatched = true;
        window.appendAlarm('alarm', 'Tool breakage', `${torque.toFixed(1)} N·m`);
      }
    } else {
      // Condition cleared — re-arm (mirrors backend's single-fire intent)
      breakageLatched = false;
    }
  }
});

// ─── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Seed rows: index.html static rows are the pre-seed (D-11 satisfied by frozen DOM).
  // We call seedRows() as a no-op here for clarity; live rows will prepend above them.
  seedRows();
});
