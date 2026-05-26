"""Heartbeat task: publishes a status frame every interval_sec to a NATS subject
that the existing main API's ServerEventManager fans out to SSE consumers.

Per CONTEXT.md D-09 (LOCKED): the payload MUST include `subtopic` keyed exactly
as `health.sparkplug.<service>` — server_event_manager.enqueue() KeyErrors on
its absence and the SSE path silently goes dark.

This module is reused by both `backend/sparkplug_bridge/main.py` (service="bridge")
and `backend/sparkplug_bridge/simulator/main.py` (service="sim") per PATTERNS.md
recommendation. Single source of truth.

Phase 2 enrichment per CONTEXT.md D-02:
  - subtopic, ts, ok, service preserved (docker healthcheck rule)
  - mqtt_connected, nats_connected, state_online, active_session_count added when
    a HostState instance is provided.
  - state=None keeps the simulator's heartbeat_loop("sim") call working without
    modification — Phase 1 schema preserved verbatim for the simulator.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

if TYPE_CHECKING:
    from .host_state import HostState

logger = logging.getLogger("sparkplug_bridge.heartbeat")


async def heartbeat_loop(
    service: str,
    state: "HostState | None" = None,
    interval_sec: float = 5.0,
) -> None:
    """Publish a heartbeat every interval_sec.

    Phase 2 enrichment per CONTEXT.md D-02:
      - subtopic, ts, ok, service preserved (docker healthcheck rule)
      - mqtt_connected, nats_connected, state_online, active_session_count added

    For service="sim" (no HostState available), state=None and the four
    new fields are omitted from the payload — Phase 1 schema preserved
    verbatim for the simulator. Only the bridge passes a real HostState.
    """
    subject = f"progress.notification.health.sparkplug.{service}"
    subtopic = f"health.sparkplug.{service}"
    logger.info("heartbeat starting: subject=%s interval=%.1fs", subject, interval_sec)
    try:
        while True:
            doc = {
                "subtopic": subtopic,
                "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "ok": True,
                "service": service,
            }
            if state is not None:
                doc.update({
                    "mqtt_connected": state.mqtt_connected,
                    "nats_connected": state.nats_connected,
                    "state_online": state.state_online,
                    "active_session_count": state.active_session_count,
                })
            payload = json.dumps(doc)
            try:
                await nats_client.publish(subject, payload)
            except Exception as e:  # noqa: BLE001 — never let heartbeat take down the main loop
                logger.warning("heartbeat publish failed: %s", e)
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("heartbeat task cancelled (service=%s)", service)
        raise
