"""Torque-overload and tool-breakage detectors for the mill-automation service.

Retargeted from the pump_anomaly dwell+latch state machine (copy — not imported).
No HTTP here — detectors are decoupled via an injected async fire callback so they
can be unit-tested without network access.

Exported classes:
  FeedState              — shared latest-value cache for feed_rate
  TorqueOverloadDetector — dwell + latch state machine (AUTO-01, D-01, D-03, D-04)
  ToolBreakageDetector   — no-dwell breakage detection (AUTO-02, D-02)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from .config import MillAutomationSettings

log = logging.getLogger("mill_automation.detectors")

# Type alias for the injected fire callback.
FireCallback = Callable[..., Awaitable[None]]


@dataclass
class FeedState:
    """Shared latest-value cache for feed_rate.

    Updated by the message router on every feed_rate message; read by
    ToolBreakageDetector.on_torque to evaluate "while feeding".  Because
    the service runs in a single asyncio event loop, no lock is needed.
    """

    last_feed_rate: float = 0.0


class TorqueOverloadDetector:
    """Dwell + latch state machine retargeted onto spindle_torque (AUTO-01).

    Mirrors pump_anomaly.PumpAnomalyAutomation.on_metric_data exactly:
    - Uses time.monotonic() (not wall-clock) for the dwell window (D-01).
    - Latch re-arms once torque drops below limit (D-04) — one Issue per
      breach episode regardless of how long the overload lasts.
    - Fires a non-critical Issue (D-08).
    """

    def __init__(self, cfg: MillAutomationSettings, fire: FireCallback) -> None:
        self._cfg = cfg
        self._fire = fire
        self._first_violation_ts: float | None = None
        self._last_fired_ts: float = 0.0
        # One-Issue-per-episode latch (D-04): once an overload episode fires, stays
        # latched until a below-limit tick clears it, so a sustained overload that
        # never drops below the limit does NOT re-fire every latch_seconds.
        self._fired: bool = False

    async def on_torque(self, value: float) -> None:
        """Process one torque reading.  Fires the overload Issue at most once per episode."""
        cfg = self._cfg
        now = time.monotonic()  # monotonic, NOT wall-clock — pump_anomaly pattern
        in_violation = isinstance(value, (int, float)) and value > cfg.torque_limit_nm

        if not in_violation:
            # Signal below limit → re-arm: clear dwell timer and the fired latch so
            # the next crossing starts a fresh episode (D-04).
            self._first_violation_ts = None
            self._fired = False
            return

        if self._first_violation_ts is None:
            # First tick above limit: start the dwell clock.
            self._first_violation_ts = now
            return

        if now - self._first_violation_ts < cfg.dwell_seconds:
            # Still within the dwell window; wait longer.
            return

        if self._fired:
            # Already fired for this episode — one Issue per breach episode (D-04).
            # The episode only ends (re-arms) when torque drops below the limit.
            return

        if now - self._last_fired_ts < cfg.latch_seconds:
            # Latch active — suppress re-fire until latch window elapses.
            return

        # Dwell elapsed, latch expired, not yet fired this episode → fire.
        await self._fire(
            title=f"Spindle torque overload: {value:.1f} N·m",
            critical=False,  # D-08: overload is not critical
            source_metric="mill-torque-overload",
        )
        self._last_fired_ts = now
        self._fired = True


class ToolBreakageDetector:
    """No-dwell tool-breakage detector: torque collapse while feeding (AUTO-02, D-02).

    Condition: spindle_torque < breakage_floor_nm AND feed_state.last_feed_rate > 0.
    No dwell — fires immediately on the first tick meeting the condition (or after
    breakage_confirm_ticks ticks for the optional guard against transients).
    Re-arms after torque recovers or feed stops (a subsequent breakage after recovery
    fires again).  Fires a critical Issue (D-08).
    """

    def __init__(
        self,
        cfg: MillAutomationSettings,
        fire: FireCallback,
        feed_state: FeedState,
    ) -> None:
        self._cfg = cfg
        self._fire = fire
        self._feed_state = feed_state
        self._below_ticks: int = 0
        self._fired: bool = False

    async def on_torque(self, value: float) -> None:
        """Process one torque reading.  May fire the tool-breakage Issue once per episode."""
        cfg = self._cfg
        # Numeric guard symmetric with TorqueOverloadDetector.on_torque (WR-02):
        # the f-string title formats value:.1f, so a non-numeric value must be
        # dropped here rather than raising downstream.
        condition = (
            isinstance(value, (int, float))
            and value < cfg.breakage_floor_nm
            and self._feed_state.last_feed_rate > 0
        )

        if condition:
            self._below_ticks += 1
            if self._below_ticks >= cfg.breakage_confirm_ticks and not self._fired:
                # Confirmed breakage — fire immediately, no dwell (D-02).
                await self._fire(
                    title=(
                        f"Tool breakage: spindle torque collapsed to {value:.1f} N·m"
                        " while feeding"
                    ),
                    critical=True,  # D-08: breakage is the more severe event
                    source_metric="mill-tool-breakage",
                )
                self._fired = True
        else:
            # Condition no longer met (torque recovered above floor or feed stopped):
            # re-arm so a subsequent breakage after recovery fires again.
            self._below_ticks = 0
            self._fired = False
