import asyncio
import json
import logging

import nats
from nats.aio.client import Client as NatsClient

logger = logging.getLogger("nats_client")
logger.setLevel(logging.INFO)

_nc: NatsClient | None = None
_loop: asyncio.AbstractEventLoop | None = None

SUBTOPIC_TO_SUBJECT = {
    "global-notification": "progress.notification.global",
    "inventory-notification": "progress.notification.inventory",
    "serial-notification": "progress.notification.serial",
    "task-notification": "progress.notification.task",
}

SUBJECT_TO_SUBTOPIC = {v: k for k, v in SUBTOPIC_TO_SUBJECT.items()}


def _subject_to_subtopic(subject: str) -> str | None:
    """Map a NATS subject back to the legacy subtopic string used by ServerEventManager."""
    return SUBJECT_TO_SUBTOPIC.get(subject)


def subtopic_to_subject(subtopic: str) -> str:
    """Convert a legacy subtopic string to a NATS subject for publishing."""
    subject = SUBTOPIC_TO_SUBJECT.get(subtopic)
    if subject:
        return subject
    return f"progress.notification.{subtopic}"


async def connect(url: str) -> NatsClient:
    global _nc, _loop
    _loop = asyncio.get_running_loop()

    async def error_cb(e):
        logger.error(f"NATS error: {e}")

    async def disconnected_cb():
        logger.warning("NATS disconnected")

    async def reconnected_cb():
        logger.warning("NATS reconnected")

    _nc = await nats.connect(
        url,
        error_cb=error_cb,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,
    )
    logger.info(f"Connected to NATS at {url}")
    return _nc


def get_nats() -> NatsClient:
    if _nc is None:
        raise RuntimeError("NATS client not connected. Call connect() first.")
    return _nc


def get_loop() -> asyncio.AbstractEventLoop:
    if _loop is None:
        raise RuntimeError("NATS event loop not set. Call connect() first.")
    return _loop


async def publish(subject: str, data: str | bytes) -> None:
    nc = get_nats()
    if isinstance(data, str):
        data = data.encode()
    await nc.publish(subject, data)


async def request(subject: str, data: str | bytes, timeout: float = 10.0) -> bytes:
    nc = get_nats()
    if isinstance(data, str):
        data = data.encode()
    response = await nc.request(subject, data, timeout=timeout)
    return response.data


async def subscribe(subject: str, cb) -> None:
    nc = get_nats()
    await nc.subscribe(subject, cb=cb)
    logger.info(f"Subscribed to {subject}")


async def drain() -> None:
    if _nc is None:
        return
    try:
        if _nc.is_connected:
            await asyncio.wait_for(_nc.drain(), timeout=5.0)
            logger.info("NATS connection drained")
        elif not _nc.is_closed:
            await _nc.close()
            logger.info("NATS connection closed (was not connected)")
    except asyncio.TimeoutError:
        logger.warning("NATS drain timed out, forcing close")
        try:
            await _nc.close()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"NATS drain error: {e}")
        try:
            if not _nc.is_closed:
                await _nc.close()
        except Exception:
            pass
