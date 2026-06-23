"""Mill-automation asyncio entrypoint.

Standalone subscriber process — NOT a FastAPI app.  No HTTP surface.
Connects its OWN NATS client (never the product API singleton) and subscribes
to the single `progress.uns.>` wildcard (ADR-0014 §2.1 / D-10).  Routes
messages by subject leaf to TorqueOverloadDetector and ToolBreakageDetector.

Run as:  python -m mill_automation
         or via Docker: CMD ["python", "-m", "mill_automation"]

AUTO-04 guarantee: this process is fully decoupled from the Sparkplug bridge.
Stopping the bridge cannot stop the automation.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys

import nats

from .config import get_config
from .detectors import FeedState, ToolBreakageDetector, TorqueOverloadDetector
from . import issue_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("mill_automation")


async def main() -> None:
    cfg = get_config()

    if not cfg.enabled:
        logger.info("Mill automation disabled (MILL_AUTO_ENABLED=false) — exiting")
        return

    token = issue_client.read_token(cfg.token_path)
    logger.info("JWT token loaded from %s", cfg.token_path)

    # Build the shared fire callback — wraps issue_client.fire_issue with cfg + token.
    async def fire(*, title: str, critical: bool, source_metric: str) -> None:
        await issue_client.fire_issue(
            cfg, token, title=title, critical=critical, source_metric=source_metric
        )

    feed_state = FeedState()
    torque_detector = TorqueOverloadDetector(cfg, fire)
    breakage_detector = ToolBreakageDetector(cfg, fire, feed_state)

    # -------------------------------------------------------------------------
    # Own NATS connection — mirrors the publisher connect_nats pattern (copied,
    # NOT imported — AUTO-04 / D-12).
    # -------------------------------------------------------------------------
    async def error_cb(e: Exception) -> None:
        logger.error("NATS error: %s", e)

    async def disconnected_cb() -> None:
        logger.warning("NATS disconnected")

    async def reconnected_cb() -> None:
        logger.warning("NATS reconnected")

    nc = await nats.connect(
        cfg.nats_url,
        error_cb=error_cb,
        disconnected_cb=disconnected_cb,
        reconnected_cb=reconnected_cb,
        reconnect_time_wait=2,
        max_reconnect_attempts=-1,
    )
    logger.info("Connected to NATS at %s", cfg.nats_url)

    # -------------------------------------------------------------------------
    # Message handler — single progress.uns.> subscription (ADR-0014 §2.1 / D-10).
    # Per-message tolerance: one malformed envelope logs and is dropped; the
    # subscription never dies (T-03-01 threat mitigation).
    # -------------------------------------------------------------------------
    async def on_msg(msg: nats.aio.msg.Msg) -> None:
        try:
            leaf = msg.subject.rsplit(".", 1)[-1]
            doc = json.loads(msg.data)
            value = doc.get("value")

            if leaf == cfg.feed_rate_leaf:
                if isinstance(value, (int, float)):
                    feed_state.last_feed_rate = float(value)
            elif leaf == cfg.torque_leaf:
                if isinstance(value, (int, float)):
                    await torque_detector.on_torque(float(value))
                    await breakage_detector.on_torque(float(value))
            # All other leaves are ignored.
        except json.JSONDecodeError as exc:
            logger.error("on_msg: JSON decode error on %s: %s", msg.subject, exc)
        except Exception:  # noqa: BLE001
            logger.exception("on_msg: unexpected error on %s", msg.subject)

    # SINGLE subscription — one wildcard covers the whole UNS (ADR-0014 §2.1).
    await nc.subscribe("progress.uns.>", cb=on_msg)
    logger.info("Subscribed to progress.uns.> — automation active")

    # -------------------------------------------------------------------------
    # Block until cancelled, then drain the connection gracefully
    # (mirrors the publisher drain_nats pattern — copied, NOT imported).
    # -------------------------------------------------------------------------
    try:
        await asyncio.Event().wait()
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Shutdown signal received — draining NATS connection")
    finally:
        try:
            if nc.is_connected:
                await asyncio.wait_for(nc.drain(), timeout=5.0)
                logger.info("NATS connection drained")
            elif not nc.is_closed:
                await nc.close()
                logger.info("NATS connection closed")
        except asyncio.TimeoutError:
            logger.warning("NATS drain timed out, forcing close")
            try:
                await nc.close()
            except Exception:
                pass
        except Exception as exc:
            logger.warning("NATS drain error: %s", exc)
            try:
                if not nc.is_closed:
                    await nc.close()
            except Exception:
                pass
