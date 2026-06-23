/**
 * controls.js — Wave 2 write path
 *
 * Responsibilities:
 *  - Initialize 5 setpoint sliders to nominal defaults (D-17)
 *  - On slider change: POST BASE+/setpoints with correct key + value
 *    (wear slider: sliderValue / 100 — Pitfall 5)
 *  - Optimistic-reflect on input; echo-confirm via uns-sample; revert on failure (D-18)
 *  - Fault buttons: #btn-snap-tool → POST /fault {fault:'snap_tool'}
 *                   #btn-hard-spot → POST /fault {fault:'hard_spot'}
 *  - #btn-reset → POST /reset; restore nominal slider values
 *  - WO ticket config injection from window.WO_LINKS (D-08)
 *
 * Threat mitigations:
 *  - T-04-09: outValue clamped to backend range before POST (defense in depth)
 *  - T-04-10: no auth on /fault — accepted for demo context (PANEL-02)
 */

const BASE = window.DEMO_TWIN_BASE_URL || '';

// ─── Slider configuration ─────────────────────────────────────────────────────
// data-key → { min, max, nominal, unit, formatFn, postKey, toPost }
// toPost: function to convert slider display-value to POST value

const SLIDER_CFG = {
  n: {
    min: 1000, max: 30000,
    sliderMin: 6000, sliderMax: 12000,
    nominal: 12000,
    unit: 'rpm',
    format: v => `${Math.round(v).toLocaleString('en')} rpm`,
    toPost: v => Number(v),
    echoLeaf: 'spindle_rpm',
    echoFromSample: v => Number(v),        // echo value is in rpm
  },
  fz: {
    min: 0.01, max: 0.5,
    sliderMin: 0.05, sliderMax: 0.30,
    nominal: 0.12,
    unit: 'mm/tooth',
    format: v => `${Number(v).toFixed(2)} mm/tooth`,
    toPost: v => Number(v),
    echoLeaf: 'feed_per_tooth',
    echoFromSample: v => Number(v),
  },
  ap: {
    min: 0.1, max: 20,
    sliderMin: 0.5, sliderMax: 8.0,
    nominal: 8.0,
    unit: 'mm',
    format: v => `${Number(v).toFixed(1)} mm`,
    toPost: v => Number(v),
    echoLeaf: 'depth_of_cut',
    echoFromSample: v => Number(v),
  },
  wear: {
    min: 0.0, max: 1.0,
    sliderMin: 0, sliderMax: 100,
    nominal: 10,   // display percent; POST as /100
    unit: '%',
    format: v => `${Math.round(v)} %`,
    toPost: v => Number(v) / 100,          // Pitfall 5: backend wants 0.0–1.0
    echoLeaf: 'tool_wear_pct',
    echoFromSample: v => Number(v),        // engine echoes wear*100 → compare as pct
  },
  coolant_temp_sp: {
    min: 0, max: 80,
    sliderMin: 0, sliderMax: 80,
    nominal: 20,
    unit: '°C',
    format: v => `${Math.round(v)} °C`,
    toPost: v => Number(v),
    echoLeaf: 'coolant_temp',
    echoFromSample: v => Number(v),
  },
};

// ─── Pending echo-confirm state ────────────────────────────────────────────────
// { [dataKey]: { postedDisplayValue: number, isDragging: boolean } | null }
const pendingConfirm = {};

// ─── Per-slider drag state ─────────────────────────────────────────────────────
// Pre-drag value captured at pointerdown to revert on POST failure
const preDragValue = {};

// ─── Debounce timers ──────────────────────────────────────────────────────────
const debounceTimers = {};
const DEBOUNCE_MS = 150;

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getBlock(dataKey) {
  return document.querySelector(`.slider-block[data-key="${dataKey}"]`);
}

function getValueEl(dataKey) {
  const block = getBlock(dataKey);
  return block ? block.querySelector('.slider-value') : null;
}

function getErrorEl(dataKey) {
  const block = getBlock(dataKey);
  return block ? block.querySelector('.slider-error') : null;
}

function getSliderEl(dataKey) {
  return document.querySelector(`input.slider[data-key="${dataKey}"]`);
}

function renderValue(dataKey, displayValue) {
  const cfg = SLIDER_CFG[dataKey];
  const el = getValueEl(dataKey);
  if (el) el.textContent = cfg.format(displayValue);
}

function showError(dataKey, msg) {
  const el = getErrorEl(dataKey);
  if (!el) return;
  el.textContent = msg;
  el.style.color = '#F0533B';
  el.style.fontFamily = 'GeistMono, monospace';
  el.style.fontSize = '10px';
  clearTimeout(el._clearTimer);
  el._clearTimer = setTimeout(() => {
    el.textContent = '';
  }, 2000);
}

function clearError(dataKey) {
  const el = getErrorEl(dataKey);
  if (el) el.textContent = '';
}

/** Clamp outValue to backend-accepted range (T-04-09) */
function clampToBackend(dataKey, postValue) {
  const cfg = SLIDER_CFG[dataKey];
  return Math.max(cfg.min, Math.min(cfg.max, postValue));
}

// ─── POST helpers ─────────────────────────────────────────────────────────────

async function postSetpoints(dataKey, displayValue) {
  const cfg = SLIDER_CFG[dataKey];
  let postValue = cfg.toPost(displayValue);
  postValue = clampToBackend(dataKey, postValue);

  // Record pending echo-confirm
  pendingConfirm[dataKey] = { postedDisplayValue: displayValue };

  try {
    const r = await fetch(BASE + '/setpoints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [dataKey]: postValue }),
    });
    if (!r.ok) {
      throw new Error(`HTTP ${r.status}`);
    }
    // Response is {"ok":true,"applied":{...}} — no further action needed;
    // echo-confirm via uns-sample will clear pendingConfirm
  } catch (err) {
    console.warn(`[controls] POST /setpoints ${dataKey} failed:`, err.message ?? err);
    pendingConfirm[dataKey] = null;

    // Revert slider + display to pre-drag value
    const revert = preDragValue[dataKey] ?? cfg.nominal;
    const sliderEl = getSliderEl(dataKey);
    if (sliderEl) sliderEl.value = revert;
    renderValue(dataKey, revert);
    showError(dataKey, 'Error — reverted');
  }
}

// ─── Slider initialization ────────────────────────────────────────────────────

function initSliders() {
  for (const [dataKey, cfg] of Object.entries(SLIDER_CFG)) {
    const sliderEl = getSliderEl(dataKey);
    if (!sliderEl) continue;

    // Set to nominal default
    sliderEl.value = cfg.nominal;
    renderValue(dataKey, cfg.nominal);
    preDragValue[dataKey] = cfg.nominal;
    pendingConfirm[dataKey] = null;

    // Track whether the debounce timer already fired for this drag gesture.
    // Prevents double-POST: if the user holds still for >DEBOUNCE_MS before
    // releasing, the debounce fires first; the subsequent `change` event must
    // not POST again.
    let debounceDidFire = false;

    // Capture pre-drag value on pointerdown
    sliderEl.addEventListener('pointerdown', () => {
      preDragValue[dataKey] = Number(sliderEl.value);
      pendingConfirm[dataKey] = null; // cancel any stale pending
      debounceDidFire = false;        // reset for this drag gesture
    });

    // Optimistic display on input (while dragging)
    sliderEl.addEventListener('input', () => {
      const v = Number(sliderEl.value);
      renderValue(dataKey, v);
      clearError(dataKey);

      // Debounced POST during drag
      clearTimeout(debounceTimers[dataKey]);
      debounceTimers[dataKey] = setTimeout(() => {
        debounceDidFire = true;
        postSetpoints(dataKey, Number(sliderEl.value));
      }, DEBOUNCE_MS);
    });

    // Final POST on change (pointer-up) — skip if debounce already fired
    sliderEl.addEventListener('change', () => {
      clearTimeout(debounceTimers[dataKey]); // cancel pending debounce (if any)
      if (!debounceDidFire) {
        // Debounce did not fire — POST the final value now
        const v = Number(sliderEl.value);
        renderValue(dataKey, v);
        clearError(dataKey);
        postSetpoints(dataKey, v);
      }
      debounceDidFire = false; // reset for next drag gesture
    });
  }
}

// ─── Echo-confirm via uns-sample ──────────────────────────────────────────────

window.addEventListener('uns-sample', (e) => {
  const { leaf, value } = e.detail;

  for (const [dataKey, cfg] of Object.entries(SLIDER_CFG)) {
    if (cfg.echoLeaf !== leaf) continue;
    const pending = pendingConfirm[dataKey];
    if (!pending) continue;

    // Convert echoed value to display-space for comparison
    const echoedDisplay = cfg.echoFromSample(value);
    const posted = pending.postedDisplayValue;

    // Compare with tolerance (floating point rounding)
    const tol = 0.01 * (cfg.sliderMax - cfg.sliderMin || 1) + 0.001;
    if (Math.abs(echoedDisplay - posted) <= tol) {
      // Confirmed — clear pending; no visual change needed (readout already shows value)
      pendingConfirm[dataKey] = null;
    }
  }
});

// ─── Fault buttons ────────────────────────────────────────────────────────────

async function postFault(faultType) {
  try {
    const r = await fetch(BASE + '/fault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fault: faultType }),
    });
    if (!r.ok) {
      throw new Error(`HTTP ${r.status}`);
    }
  } catch (err) {
    console.warn(`[controls] POST /fault ${faultType} failed:`, err.message ?? err);
    // No second alarm row — the row was already prepended before the POST
    showFaultError(faultType, 'Error — POST failed');
  }
}

function showFaultError(faultType, msg) {
  // Show inline error near the relevant button
  const btnId = faultType === 'snap_tool' ? 'btn-snap-tool' : 'btn-hard-spot';
  const btn = document.getElementById(btnId);
  if (!btn) return;
  // Use a data attribute to track the error overlay
  let errEl = btn.querySelector('.fault-inline-error');
  if (!errEl) {
    errEl = document.createElement('span');
    errEl.className = 'fault-inline-error';
    errEl.style.cssText = 'display:block;color:#F0533B;font-size:10px;font-family:GeistMono,monospace;margin-top:2px';
    btn.appendChild(errEl);
  }
  errEl.textContent = msg;
  clearTimeout(errEl._clearTimer);
  errEl._clearTimer = setTimeout(() => { errEl.textContent = ''; }, 2000);
}

function initFaultButtons() {
  const btnSnap = document.getElementById('btn-snap-tool');
  const btnHard = document.getElementById('btn-hard-spot');
  const btnReset = document.getElementById('btn-reset');

  if (btnSnap) {
    btnSnap.addEventListener('click', () => {
      // Set state flag so state-bar shows ALARM
      if (window.twinTelemetry) window.twinTelemetry.snapTool = true;

      // Append alarm row FIRST (controls.js calls alarms.js via window.appendAlarm)
      if (typeof window.appendAlarm === 'function') {
        window.appendAlarm('alarm', 'Snap tool injected — torque collapse', '');
      }

      // POST fault (error appends no second row)
      postFault('snap_tool');
    });
  }

  if (btnHard) {
    btnHard.addEventListener('click', () => {
      // Append warn row FIRST
      if (typeof window.appendAlarm === 'function') {
        window.appendAlarm('warn', 'Hard-spot injected — torque spike', '');
      }

      // POST fault
      postFault('hard_spot');
    });
  }

  if (btnReset) {
    btnReset.addEventListener('click', async () => {
      try {
        const r = await fetch(BASE + '/reset', { method: 'POST' });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);

        // Restore all sliders to nominal defaults
        for (const [dataKey, cfg] of Object.entries(SLIDER_CFG)) {
          const sliderEl = getSliderEl(dataKey);
          if (sliderEl) sliderEl.value = cfg.nominal;
          renderValue(dataKey, cfg.nominal);
          preDragValue[dataKey] = cfg.nominal;
          pendingConfirm[dataKey] = null;
          clearError(dataKey);
        }

        // Clear snapTool state
        if (window.twinTelemetry) window.twinTelemetry.snapTool = false;

        // No alarm row for reset per spec

      } catch (err) {
        console.warn('[controls] POST /reset failed:', err.message ?? err);
        // Surface error on the reset button itself (not snap_tool)
        const btn = document.getElementById('btn-reset');
        if (btn) {
          let errEl = btn.querySelector('.fault-inline-error');
          if (!errEl) {
            errEl = document.createElement('span');
            errEl.className = 'fault-inline-error';
            errEl.style.cssText = 'display:block;color:#F0533B;font-size:10px;font-family:GeistMono,monospace;margin-top:2px';
            btn.appendChild(errEl);
          }
          errEl.textContent = 'Error — reset failed';
          clearTimeout(errEl._clearTimer);
          errEl._clearTimer = setTimeout(() => { errEl.textContent = ''; }, 2000);
        }
      }
    });
  }
}

// ─── WO ticket config injection (D-08) ────────────────────────────────────────

function injectWoLinks() {
  const links = window.WO_LINKS;
  if (!links) return;

  // Set #wo-kv-operation to the operation ID from config (not hardcoded)
  const opEl = document.getElementById('wo-kv-operation');
  if (opEl) opEl.textContent = links.operation;

  // Carry link keys as data-link-* attributes on the ticket element
  // so Phase 5 can read/update without touching markup
  const ticket = document.querySelector('.wo-ticket');
  if (ticket) {
    ticket.dataset.linkSerial     = links.serial     || '';
    ticket.dataset.linkWorkOrder  = links.work_order || '';
    ticket.dataset.linkOperation  = links.operation  || '';
  }

  // Also set the hidden #wo-order span to the work_order key
  const woOrderEl = document.getElementById('wo-order');
  if (woOrderEl) woOrderEl.textContent = links.work_order || '';
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initSliders();
  initFaultButtons();
  injectWoLinks();
});
