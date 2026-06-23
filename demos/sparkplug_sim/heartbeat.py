"""Heartbeat task for the simulator — publishes a status frame every interval_sec
to a NATS subject the API's ServerEventManager fans out to SSE consumers.

The payload MUST include `subtopic` keyed exactly as `health.sparkplug.<service>`
(server_event_manager.enqueue() KeyErrors on its absence and the SSE path goes dark).

Local copy of the bridge's heartbeat (backend/sparkplug_bridge/heartbeat.py). The
simulator was separated from the bridge package; this small module was the only
thing they shared. Kept in sync by contract, not by import. The sim has no
HostState, so the bridge's optional enrichment fields are omitted here.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

logger = logging.getLogger("sparkplug_sim.heartbeat")


async def heartbeat_loop(service: str, interval_sec: float = 5.0) -> None:
    """Publish a heartbeat every interval_sec (sim schema — no HostState fields)."""
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
            payload = json.dumps(doc)
            try:
                await nats_client.publish(subject, payload)
            except Exception as e:  # noqa: BLE001 — never let heartbeat take down the main loop
                logger.warning("heartbeat publish failed: %s", e)
            await asyncio.sleep(interval_sec)
    except asyncio.CancelledError:
        logger.info("heartbeat task cancelled (service=%s)", service)
        raise
