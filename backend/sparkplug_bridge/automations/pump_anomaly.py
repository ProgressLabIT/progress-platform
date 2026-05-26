"""ADR-0010 hardcoded automation: pump-3 vibration → IssueCreatedEvent.

Subscribes to progress.sparkplug.plant1.edge1.pump3.metric.vibration.data
(ADR-0002). 5-second dwell + 60-second latch over THRESHOLD=100.0 mm/s
fires POST /api/event with event_type=ISSUE_CREATED linked to WO-DEMO-001
and PH-DEMO-001. Replaced post-demo by Bytewax (ADR-0009).

Latch is in-memory only — bridge restart resets state (accepted by ADR-0010).
"""
import logging
import os
import time

# httpx is optional at module-import time so the simulator can import THRESHOLD
# for cross-validation without carrying the http dep. The bridge image installs
# httpx (see backend/sparkplug_bridge/requirements.txt); if _fire ever runs in
# an environment without httpx we want a clear error there, not at import.
try:
    import httpx
except ImportError:
    httpx = None

log = logging.getLogger("sparkplug_bridge.automations.pump_anomaly")

# ADR-0010 lock — must equal scenario.yaml ``pump3_anomaly.threshold_mm_s``.
# scenario.py raises at simulator startup if the two diverge.
TARGET_METRIC_ID = "plant1.edge1.pump3.Vibration"
THRESHOLD = 100.0
# Dwell and latch are env-overridable for fast-iteration testing. Defaults
# are the ADR-0010 demo values; lower DWELL to ~1 when running a fast-scenario
# sim where Vibration is above threshold only briefly.
DWELL_SECONDS = float(os.environ.get("PUMP_ANOMALY_DWELL_SECONDS", "5"))
LATCH_SECONDS = float(os.environ.get("PUMP_ANOMALY_LATCH_SECONDS", "60"))

# Link targets — env-driven so the same image runs against a demo dataset
# (defaults WO-DEMO-001 / PH-DEMO-001) or any other dataset (override via
# PUMP_ANOMALY_LINKED_* env vars). Read at import time; restart bridge to
# pick up changes. Identity is NOT env-driven — it comes from the JWT in
# the Authorization header, which the API decodes via verify_token.
LINKED_WO_KEY = os.environ.get("PUMP_ANOMALY_LINKED_WO_KEY", "WO-DEMO-001")
LINKED_PHASE_KEY = os.environ.get("PUMP_ANOMALY_LINKED_PHASE_KEY", "PH-DEMO-001")
# Required by IssueWithLinks validator ("Issue must have type associated").
# Demo dataset bundle should ship a known IssueType _key; pick one with a
# generic equipment-anomaly meaning. No default — set per environment.
ISSUE_TYPE_KEY = os.environ.get("PUMP_ANOMALY_ISSUE_TYPE_KEY", "")
# Required by IssueWithLinks (`created_by: str = Field(...)`). The API uses
# the JWT for auth, but the Issue document records its own `created_by` —
# this value MUST match the JWT's user so audit trails reconcile. The
# operator sets both alongside the JWT in the demo dataset bundle; the
# bridge does not decode the token.
CREATED_BY = os.environ.get("PUMP_ANOMALY_CREATED_BY", "User/USR-SPARKPLUG-BRIDGE")
# user_key + user_session_key are stored on the Event document for audit
# and downstream UI lookups (webapp's IssueDetail/history tab joins these
# against User and UserSession collections). Same rule as CREATED_BY:
# operator-configured per environment, NOT decoded from the JWT.
USER_KEY = os.environ.get("PUMP_ANOMALY_USER_KEY", "USR-SPARKPLUG-BRIDGE")
USER_SESSION_KEY = os.environ.get("PUMP_ANOMALY_USER_SESSION_KEY", "sparkplug-bridge")

LINKED_TO = [
    {"type": "work_order", "key": LINKED_WO_KEY},
    {"type": "phase", "key": LINKED_PHASE_KEY},
]


def _id_from_envelope(payload: dict) -> str:
    """Build metric_id from group/edge/device/name (case-preserving — RESEARCH §Pitfall 5)."""
    parts = [
        payload.get("group"),
        payload.get("edge"),
        payload.get("device"),
        payload.get("name"),
    ]
    return ".".join(p for p in parts if p)


class PumpAnomalyAutomation:
    """ADR-0010 dwell + latch state machine. Call on_metric_data per envelope."""

    def __init__(self, api_base_url: str, token_path: str):
        self.api_base_url = api_base_url
        self._token = self._read_token(token_path)
        self._first_violation_ts: float | None = None
        self._last_fired_ts: float = 0.0

    @staticmethod
    def _read_token(path: str) -> str:
        with open(path, "r") as f:
            return f.read().strip()

    async def on_metric_data(self, payload: dict) -> None:
        if os.environ.get("SPARKPLUG_AUTOMATIONS_ENABLED", "true").lower() != "true":
            return
        metric_id = payload.get("metric_id") or _id_from_envelope(payload)
        if metric_id != TARGET_METRIC_ID:
            return
        value = payload.get("value")
        now = time.monotonic()  # monotonic, not wall-clock — RESEARCH A1
        in_violation = isinstance(value, (int, float)) and value > THRESHOLD

        if not in_violation:
            self._first_violation_ts = None
            return
        if self._first_violation_ts is None:
            self._first_violation_ts = now
            return
        if now - self._first_violation_ts < DWELL_SECONDS:
            return
        if now - self._last_fired_ts < LATCH_SECONDS:
            return

        await self._fire(payload)
        self._last_fired_ts = now
        self._first_violation_ts = None

    async def _fire(self, payload: dict) -> None:
        # FLAT body — RESEARCH §Pitfall 2 (issue_data at top level, not under "info").
        body = {
            "event_type": "ISSUE_CREATED",
            "user_key": USER_KEY,
            "user_session_key": USER_SESSION_KEY,
            "primary": True,
            "issue_data": {
                "issue_type_key": ISSUE_TYPE_KEY,
                "created_by": CREATED_BY,
                "critical": False,
                "title": f"Pump 3 vibration anomaly: {payload['value']:.1f} mm/s",
                "linked_to": LINKED_TO,
            },
            "source_metric": "pump-anomaly-automation",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(
                    f"{self.api_base_url}/event",
                    headers={"Authorization": f"Bearer {self._token}"},
                    json=body,
                )
        except httpx.HTTPError as e:
            log.error("automation fire transport error: %s", e)
            return
        if r.status_code >= 300:
            log.error("automation fire failed: status=%d body=%s", r.status_code, r.text)
        else:
            log.info("automation fired: issue from %s = %s", TARGET_METRIC_ID, payload.get("value"))
