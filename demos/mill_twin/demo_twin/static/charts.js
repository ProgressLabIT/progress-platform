/**
 * charts.js — Wave 2 read path
 *
 * Responsibilities:
 *  - Init three ECharts line instances on #chart-power / #chart-mrr / #chart-torque
 *  - Export pushPoint(leaf, value) for telemetry.js to call
 *  - 60-second rolling window (MAX_POINTS = 300 at 5 Hz)
 *  - rAF-coalesced setOption (never per-message synchronous)
 *  - Spindle Torque chart: fixed 0–60 N·m axis + dashed 45 N·m markLine (D-21 / PANEL-03/04)
 *  - Torque line + badge: green below 45, red at/over 45
 *  - Pre-telemetry "Connecting…" placeholder until first point per chart (D-17)
 *
 * ECharts global is already available from the UMD bundle loaded before this module.
 */

const MAX_POINTS = 300; // 60 s at 5 Hz

// ─── Color constants (match CSS tokens) ───────────────────────────────────────

const COLOR_ACCENT      = '#4A9FD8'; // power chart line
const COLOR_OK          = '#35C98A'; // mrr chart line + torque when <45
const COLOR_ALARM       = '#F0533B'; // torque alarm / markLine
const COLOR_AXIS_LABEL  = '#5E6A78';
const COLOR_SPLIT_LINE  = '#1F2630';
const COLOR_BG_TRANSPARENT = 'transparent';
const TORQUE_LIMIT      = 45;

// ─── Chart descriptor table ───────────────────────────────────────────────────

// Each chart owns: ECharts instance, data buffer, dirty flag, rAF handle, latest value
const charts = {
  spindle_power: {
    id:          'chart-power',
    valId:       'chart-power-val',
    unit:        'kW',
    lineColor:   COLOR_ACCENT,
    fixedY:      null, // auto-scale
    markLine:    null,
    instance:    null,
    xData:       [],
    yData:       [],
    raf:         null,
  },
  mrr: {
    id:          'chart-mrr',
    valId:       'chart-mrr-val',
    unit:        'cm³/min',
    lineColor:   COLOR_OK,
    fixedY:      null,
    markLine:    null,
    instance:    null,
    xData:       [],
    yData:       [],
    raf:         null,
  },
  spindle_torque: {
    id:          'chart-torque',
    valId:       'chart-torque-val',
    unit:        'N·m',
    lineColor:   COLOR_OK,  // starts green; recolored per push
    fixedY:      { min: 0, max: 60 },
    markLine:    {
      silent:    true,
      symbol:    ['none', 'none'],
      lineStyle: { color: COLOR_ALARM, type: 'dashed', width: 1.5 },
      data:      [{ yAxis: 45 }],
    },
    instance:    null,
    xData:       [],
    yData:       [],
    raf:         null,
  },
};

// ─── Build initial ECharts option ─────────────────────────────────────────────

function buildInitialOption(cfg, lineColor) {
  const yAxis = {
    type:       'value',
    axisLabel:  {
      color:      COLOR_AXIS_LABEL,
      fontFamily: 'Geist Mono, monospace',
      fontSize:   9,
    },
    splitLine:  { lineStyle: { color: COLOR_SPLIT_LINE } },
    axisLine:   { show: false },
    axisTick:   { show: false },
  };
  if (cfg.fixedY) {
    yAxis.min = cfg.fixedY.min;
    yAxis.max = cfg.fixedY.max;
  }

  const series = {
    type:        'line',
    data:        [],
    symbol:      'none',
    smooth:      false,
    lineStyle:   { color: lineColor, width: 1.5 },
    itemStyle:   { color: lineColor },
    areaStyle:   null,
    animation:   false,
  };
  if (cfg.markLine) {
    series.markLine = cfg.markLine;
  }

  return {
    backgroundColor: COLOR_BG_TRANSPARENT,
    grid: {
      top:          8,
      right:        8,
      bottom:       4,
      left:         36,
      containLabel: false,
    },
    xAxis: {
      type:        'category',
      data:        [],
      boundaryGap: false,
      axisLabel:   { show: false },
      axisLine:    { lineStyle: { color: COLOR_SPLIT_LINE } },
      axisTick:    { show: false },
      splitLine:   { show: false },
    },
    yAxis,
    series: [series],
  };
}

// ─── Pre-telemetry placeholder overlay ───────────────────────────────────────

/**
 * Add a CSS overlay div to the chart container while no data has arrived.
 * Removed on first pushPoint for that chart.
 */
function addPlaceholder(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  // Avoid duplicate
  if (container.querySelector('.chart-placeholder')) return;

  const div = document.createElement('div');
  div.className = 'chart-placeholder';
  div.style.cssText = [
    'position:absolute',
    'inset:0',
    'display:flex',
    'align-items:center',
    'justify-content:center',
    `color:${COLOR_AXIS_LABEL}`,
    'font-family:Geist Mono, monospace',
    'font-size:11px',
    'pointer-events:none',
    'z-index:1',
  ].join(';');
  div.textContent = 'Connecting…';

  // Container must be positioned for absolute child
  container.style.position = 'relative';
  container.appendChild(div);
}

function removePlaceholder(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const ph = container.querySelector('.chart-placeholder');
  if (ph) ph.remove();
}

// ─── Init all charts after DOM ready ─────────────────────────────────────────

function initCharts() {
  for (const [leaf, cfg] of Object.entries(charts)) {
    const el = document.getElementById(cfg.id);
    if (!el) {
      console.warn(`[charts] container #${cfg.id} not found`);
      continue;
    }

    cfg.instance = echarts.init(el, null, { renderer: 'canvas' });
    cfg.instance.setOption(buildInitialOption(cfg, cfg.lineColor));

    // Pre-telemetry placeholder
    addPlaceholder(cfg.id);
  }

  // Handle window resize
  window.addEventListener('resize', () => {
    for (const cfg of Object.values(charts)) {
      if (cfg.instance) cfg.instance.resize();
    }
  });

  // Dispose ECharts instances on unload to free canvas GPU memory
  window.addEventListener('pagehide', () => {
    for (const cfg of Object.values(charts)) {
      if (cfg.instance) {
        cfg.instance.dispose();
        cfg.instance = null;
      }
    }
  });
}

// ─── pushPoint — exported API consumed by telemetry.js ────────────────────────

/**
 * Append a new sample for the given leaf; coalesce chart updates via rAF.
 * Only handles spindle_power, mrr, spindle_torque (Pitfall 7 guard).
 *
 * @param {string} leaf   - subject leaf name (identity token)
 * @param {number} value  - numeric sample value (already validated by telemetry.js)
 */
export function pushPoint(leaf, value) {
  const cfg = charts[leaf];
  if (!cfg || !cfg.instance) return;

  // Remove placeholder on first data point
  if (cfg.xData.length === 0) {
    removePlaceholder(cfg.id);
  }

  // Rolling window
  const now = new Date().toLocaleTimeString('en-GB', { hour12: false });
  cfg.xData.push(now);
  cfg.yData.push(value);
  if (cfg.xData.length > MAX_POINTS) {
    cfg.xData.shift();
    cfg.yData.shift();
  }

  // Update value badge
  updateBadge(cfg, value);

  // rAF coalescing — at most one setOption per animation frame
  if (!cfg.raf) {
    cfg.raf = requestAnimationFrame(() => {
      flushChart(leaf);
    });
  }
}

/** Update the card value badge (textContent only — T-04-06) */
function updateBadge(cfg, value) {
  const el = document.getElementById(cfg.valId);
  if (!el) return;

  // Format value
  let text;
  if (cfg.unit === 'kW') {
    text = `${value.toFixed(1)} ${cfg.unit}`;
  } else if (cfg.unit === 'cm³/min') {
    text = `${value.toFixed(0)} ${cfg.unit}`;
  } else {
    // N·m
    text = `${value.toFixed(1)} ${cfg.unit}`;
  }
  el.textContent = text;

  // Torque badge coloring: green below limit, red at/over
  if (cfg.id === 'chart-torque') {
    el.style.color = value < TORQUE_LIMIT ? COLOR_OK : COLOR_ALARM;
  }
}

/** Flush buffered data to ECharts via setOption (rAF callback) */
function flushChart(leaf) {
  const cfg = charts[leaf];
  cfg.raf = null;

  if (!cfg.instance || cfg.xData.length === 0) return;

  // For torque: recolor the line depending on latest value
  const latestValue = cfg.yData[cfg.yData.length - 1];
  const lineColor = (cfg.id === 'chart-torque')
    ? (latestValue < TORQUE_LIMIT ? COLOR_OK : COLOR_ALARM)
    : cfg.lineColor;

  cfg.instance.setOption({
    xAxis: { data: cfg.xData },
    series: [{
      data:      cfg.yData,
      lineStyle: { color: lineColor },
      itemStyle: { color: lineColor },
    }],
  });
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCharts);
} else {
  // DOMContentLoaded already fired (module scripts can execute late)
  initCharts();
}
