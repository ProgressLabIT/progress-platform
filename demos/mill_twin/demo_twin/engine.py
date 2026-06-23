"""Demo-twin physics engine.

Implements the mechanistic cutting-force model for the aerospace mill gantry
twin.  EngineState holds all setpoints, fault flags, and per-tick carry-forward
values.  compute_tick() is a pure-function-like step that mutates state in place
and returns the 13-signal set (D-02 + coolant reservoir level) as
``dict[leaf, (value, unit)]``.

Import contract (PUB-03): this module is intentionally free of MQTT and
Sparkplug dependencies — the twin is a protocol-neutral service.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from .physics import first_order_lag, pink_walk  # noqa: F401 (reset_rng imported by callers)

log = logging.getLogger("demo_twin.engine")

# ---------------------------------------------------------------------------
# Model constants  (FORMULA IS SOURCE OF TRUTH — verified from METRICS-KPIS.md)
# ---------------------------------------------------------------------------
Z: int = 4                          # number of teeth (63 mm face mill)
KC: float = 700.0                   # specific cutting force, N/mm² (Al 7075-T6)
ETA: float = 0.82                   # spindle mechanical efficiency
RATED_POWER_KW: float = 200.0       # Modig spindle rated power (kW)

# Fault model values (D-08, D-09 — METRICS-KPIS.md §4/§6)
AIR_CUT_FLOOR: float = 2.0          # N·m — snap_tool collapse target (air-cutting noise floor)
T_NOMINAL: float = 27.4             # N·m — formula output at OP-20 nominal (ap=8, ae=50, fz=0.12, n=15000, wear=0.10)
MRR_NOMINAL_CM3: float = 2880.0     # cm³/min — geometric MRR at the same nominal (ap·ae·fz·Z·n / 1000)
HARD_SPOT_ADDITIVE: float = 2.5 * T_NOMINAL   # ~68.5 N·m additive spike → ~96 N·m total (~3.5× nominal)
HARD_SPOT_DECAY_TICKS: int = 10     # countdown ticks (2 s at 5 Hz, per D-09)

# Lag / noise tuning (Claude's discretion per RESEARCH.md recommended defaults)
TAU_TORQUE: float = 0.4             # s — torque first-order lag (fast enough to see breakage clearly)
TAU_TEMP: float = 15.0              # s — spindle temperature thermal lag (slow, physical)
SIGMA_TORQUE: float = 0.8           # N·m — pink-walk micro-noise on torque (~3% of nominal)
SIGMA_COOLANT: float = 0.5          # l/min — pink-walk noise on coolant flow (~1% ripple)

# Coolant reservoir level — a monotonic float-sensor signal, NOT the flow rate.
# Drains each tick (consumption); refilled to full only on POST /reset (new EngineState).
COOLANT_TANK_FULL: float = 100.0       # % — reservoir level at shift start / reset
COOLANT_TANK_FLOOR: float = 20.0       # % — low-level floor (won't drain below)
COOLANT_DRAIN_PCT_PER_S: float = 0.15  # %/s — deterministic drain (~9%/min)

DT: float = 0.2                     # s — physics tick interval (5 Hz)


# ---------------------------------------------------------------------------
# Signal table — 13 leaves (12 D-02 + coolant_tank_pct) with exact unit strings
# ---------------------------------------------------------------------------

# Maps each NATS subject leaf to its unit string.  Kept as a tuple list to
# preserve declaration order; used only for documentation / future iteration.
SIGNAL_TABLE: list[tuple[str, str]] = [
    # derived (from cutting model)
    ("spindle_torque",    "N·m"),
    ("spindle_power",     "kW"),
    ("mrr",               "cm³/min"),
    ("feed_rate",         "mm/min"),
    ("spindle_load_pct",  "%"),
    # health (simulated)
    ("spindle_temp",      "°C"),
    ("coolant_flow",      "l/min"),
    ("coolant_tank_pct",  "%"),
    # echoed setpoints
    ("spindle_rpm",       "rpm"),
    ("feed_per_tooth",    "mm/tooth"),
    ("depth_of_cut",      "mm"),
    ("tool_wear_pct",     "%"),
    ("coolant_temp",      "°C"),
]


# ---------------------------------------------------------------------------
# Engine state
# ---------------------------------------------------------------------------

@dataclass
class EngineState:
    """Mutable per-tick state for the twin's physics engine.

    Setpoints are the operator-driven control inputs.  Fault flags are set by
    POST /fault and cleared by POST /reset.  Carry-forward fields are updated
    in place by compute_tick() on every tick.

    Default values are the OP-20 semi-finish nominal (restored by POST /reset).
    """
    # setpoints — torque levers (D-12)
    ap: float = 8.0           # axial depth of cut, mm
    ae: float = 50.0          # radial width of cut, mm
    fz: float = 0.12          # feed per tooth, mm/tooth
    n: float = 15000.0        # spindle RPM
    wear: float = 0.10        # tool wear fraction 0..1 (Kc multiplier)

    # setpoint — monitored only, NOT a torque lever (D-12)
    coolant_temp_sp: float = 20.0   # coolant temperature setpoint, °C

    # fault state (D-08, D-09)
    snap_tool: bool = False         # latched — stays broken until POST /reset
    hard_spot_ticks: int = 0        # countdown; >0 = transient spike active

    # per-tick carry-forward (initialised at OP-20 nominal)
    torque_prev: float = T_NOMINAL
    mrr_prev: float = MRR_NOMINAL_CM3   # cm³/min, lagged; collapses to 0 on snap_tool
    spindle_temp_prev: float = 38.0
    coolant_flow_prev: float = 45.0
    coolant_tank_prev: float = COOLANT_TANK_FULL   # reservoir %, drains each tick


# ---------------------------------------------------------------------------
# Physics tick
# ---------------------------------------------------------------------------

def compute_tick(state: EngineState, dt: float = DT) -> dict[str, tuple[float, str]]:
    """Advance the physics engine by one tick and return 13 signal (value, unit) pairs.

    Mutates *state* in place (torque_prev, mrr_prev, spindle_temp_prev, coolant_flow_prev,
    coolant_tank_prev, hard_spot_ticks).  The caller owns the state object and must not share it
    across concurrent tasks without an appropriate lock.

    Formula source of truth (METRICS-KPIS.md §3 + RESEARCH.md §Derived Signal Formulas):
      Kc_eff = KC * (1 + 0.5 * wear)
      vf     = fz * Z * n                  # mm/min
      MRR    = ap * ae * vf                # mm³/min
      Pc     = MRR * Kc_eff / (60e6 * η)  # kW
      T      = 9549 * Pc / n               # N·m

    Snap-tool semantics: a broken tool removes no material, so MRR collapses to ~0
    (smoothly, lagged like torque) alongside T / power / load.  feed_rate is commanded
    axis motion and does NOT collapse — the table keeps feeding the broken tool.

    Pitfall 7: now_ms() is wall-clock and is NOT called here.  The NATS publish
    layer (Plan 03) stamps `ts` so the determinism guarantee (TWIN-04) applies
    to signal values, not timestamps.
    """
    # --- mechanistic cutting model ---
    Kc_eff: float = KC * (1.0 + 0.5 * state.wear)
    vf: float = state.fz * Z * state.n                    # mm/min  → feed_rate
    MRR_mm3: float = state.ap * state.ae * vf             # mm³/min
    Pc_kw: float = (MRR_mm3 * Kc_eff) / (60.0e6 * ETA)   # kW
    T_setpoint: float = 9549.0 * Pc_kw / state.n          # N·m

    # --- fault overrides on setpoint ---
    if state.snap_tool:                         # D-08: latched collapse to air-cut floor
        T_setpoint = AIR_CUT_FLOOR

    if state.hard_spot_ticks > 0:              # D-09: transient additive spike (pre-lag)
        T_setpoint += HARD_SPOT_ADDITIVE
        state.hard_spot_ticks -= 1

    # --- first-order lag + pink noise ---
    T: float = first_order_lag(state.torque_prev, T_setpoint, TAU_TORQUE, dt)
    T = pink_walk(T, sigma=SIGMA_TORQUE)
    state.torque_prev = T

    # --- derived signals (consistent with T, not back-derived independently) ---
    Pc_actual: float = T * state.n / 9549.0                         # kW
    # Actual material removal collapses on snap_tool (broken tool removes nothing);
    # otherwise it tracks the commanded geometric rate.  Lagged with the torque time
    # constant so the collapse is smooth and coincident with the torque drop.
    mrr_target_cm3: float = 0.0 if state.snap_tool else (MRR_mm3 / 1000.0)
    state.mrr_prev = first_order_lag(state.mrr_prev, mrr_target_cm3, TAU_TORQUE, dt)
    mrr_cm3: float = state.mrr_prev                                  # cm³/min (→0 on snap_tool)
    feed_rate: float = vf                                            # mm/min  (commanded; unaffected by snap)
    spindle_load_pct: float = (Pc_actual / RATED_POWER_KW) * 100.0  # %

    # --- health signals ---
    T_load_target: float = 38.0 + 30.0 * (spindle_load_pct / 100.0)
    state.spindle_temp_prev = first_order_lag(
        state.spindle_temp_prev, T_load_target, TAU_TEMP, dt
    )
    state.coolant_flow_prev = max(
        20.0, min(100.0, pink_walk(state.coolant_flow_prev, sigma=SIGMA_COOLANT))
    )
    # coolant reservoir drains monotonically (consumption); refilled on reset only
    state.coolant_tank_prev = max(
        COOLANT_TANK_FLOOR, state.coolant_tank_prev - COOLANT_DRAIN_PCT_PER_S * dt
    )

    log.debug(
        "tick: T=%.2f N·m  Pc=%.2f kW  MRR=%.1f cm³/min  load=%.1f%%",
        T, Pc_actual, mrr_cm3, spindle_load_pct,
    )

    return {
        # derived
        "spindle_torque":   (T,                       "N·m"),
        "spindle_power":    (Pc_actual,                "kW"),
        "mrr":              (mrr_cm3,                  "cm³/min"),
        "feed_rate":        (feed_rate,                "mm/min"),
        "spindle_load_pct": (spindle_load_pct,         "%"),
        # health (simulated)
        "spindle_temp":     (state.spindle_temp_prev,  "°C"),
        "coolant_flow":     (state.coolant_flow_prev,  "l/min"),
        "coolant_tank_pct": (state.coolant_tank_prev,  "%"),
        # echoed setpoints
        "spindle_rpm":      (state.n,                  "rpm"),
        "feed_per_tooth":   (state.fz,                 "mm/tooth"),
        "depth_of_cut":     (state.ap,                 "mm"),
        "tool_wear_pct":    (state.wear * 100.0,       "%"),
        "coolant_temp":     (state.coolant_temp_sp,    "°C"),
    }
