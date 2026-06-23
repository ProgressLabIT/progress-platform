"""Numeric helpers for the demo-twin physics engine.

Sibling copy of the bridge simulator's physics helpers — kept flat so the
twin's Docker build context (COPY demo_twin/ /app/demo_twin/) works without
an additional COPY for the bridge simulator directory.
This file must remain free of MQTT and Sparkplug imports (PUB-03).
"""
import math
import random
import time as _time

# Single seeded RNG; `make demo-reset` (Phase 5+) re-seeds via reset().
_RNG = random.Random(0xDEADBEEF)


def reset_rng(seed: int = 0xDEADBEEF) -> None:
    """Re-seed the simulator RNG for deterministic rehearsals."""
    _RNG.seed(seed)


def pink_walk(prev: float, sigma: float = 1.0, bias: float = 0.0) -> float:
    """Pink-noise-ish random walk around `prev`, with optional drift `bias`.

    Implementation: prev + bias + N(0, sigma) clipped to ±3*sigma to avoid runaway.
    """
    delta = _RNG.gauss(0.0, sigma)
    delta = max(-3.0 * sigma, min(3.0 * sigma, delta))
    return prev + bias + delta


def first_order_lag(prev: float, setpoint: float, tau_seconds: float, dt_seconds: float) -> float:
    """Discrete first-order lag toward `setpoint` with time constant `tau_seconds`.

    new = prev + (setpoint - prev) * (1 - exp(-dt / tau))
    """
    if tau_seconds <= 0:
        return setpoint
    alpha = 1.0 - math.exp(-dt_seconds / tau_seconds)
    return prev + (setpoint - prev) * alpha


def monotonic_inc(prev: float, rate_per_second: float, dt_seconds: float) -> float:
    """Monotonic counter increment: prev + rate * dt (no noise)."""
    return prev + rate_per_second * dt_seconds


def linear_ramp(start_value: float, slope_per_second: float, elapsed_sec: float) -> float:
    """Deterministic linear ramp.

    Per ADR-0007 § Scenario timeline + § Amendment 2026-04-29: at t=2:30
    vibration begins linearly increasing at the slope loaded from
    scenario.yaml `pump3_anomaly.slope_mm_s_per_sec` (default 1.0). The
    cross of `pump3_anomaly.threshold_mm_s` (default 100.0) happens at
    t≈3:48 deterministically (no randomness in the ramp window).
    """
    return start_value + slope_per_second * elapsed_sec


def now_ms() -> int:
    """UTC milliseconds — wall-clock epoch ms (NOT deterministic by design)."""
    return int(_time.time() * 1000)
