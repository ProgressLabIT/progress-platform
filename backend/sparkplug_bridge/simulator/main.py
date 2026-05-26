"""Sparkplug simulator service — asyncio entrypoint.

Per CONTEXT.md D-01..D-04 + ADR-0007:
  - One container, one process, one image.
  - One aiomqtt client PER EDGE so each edge's LWT (NDEATH) fires independently
    if that edge's connection drops (RESEARCH §Open Question #1 — preferred
    because it faithfully models real Sparkplug edge gateways).
  - The bridge package's heartbeat module is reused (PATTERNS.md "DRY wins").
"""
import asyncio
import logging
import sys

from aiomqtt import Client, MqttError, ProtocolVersion, Will

from utils import nats_client  # backend/api/utils/nats_client.py via PYTHONPATH

from sparkplug_bridge.heartbeat import heartbeat_loop  # SHARED with bridge

from .config import get_config
from .encoder import build_ndeath_will
from .scenario import ScenarioRunner, load_scenario_params
from .topology import GROUP_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("sparkplug_sim")

_RECONNECT_INTERVAL_SEC = 5

# ADR-0007 § Implementation tooling — host id `sparkplug_sim` publishes
# its retained STATE so a fresh subscriber always sees an "online" beacon.
# The spike retained-STATE test uses this as the broker's retained-store probe.
_HOST_ID = "sparkplug_sim"
_HOST_STATE_TOPIC = f"spBv1.0/STATE/{_HOST_ID}"


async def _publish_host_state(cfg) -> None:
    """Connect briefly, publish the retained host-STATE beacon, disconnect.

    Retained QoS 1 with an LWT inverse so a non-graceful drop also flips the
    beacon to ``{"online":false}`` for any later subscriber.
    """
    will = Will(
        topic=_HOST_STATE_TOPIC,
        payload=b'{"online":false}',
        qos=1,
        retain=True,
    )
    client = Client(
        hostname=cfg.mqtt_host,
        port=cfg.mqtt_port,
        identifier=f"{_HOST_ID}-host-state",
        protocol=ProtocolVersion.V311,
        will=will,
        clean_session=True,
    )
    async with client:
        await client.publish(
            _HOST_STATE_TOPIC,
            payload=b'{"online":true}',
            qos=1,
            retain=True,
        )
    logger.info("published retained host STATE topic=%s", _HOST_STATE_TOPIC)


async def _run_one_session(cfg, runner: ScenarioRunner) -> None:
    """Open per-edge aiomqtt clients (each with its own LWT) and run the
    scenario inside an asyncio.TaskGroup. Returns when any edge raises MqttError
    (caught by the outer reconnect loop in main())."""
    edge_clients: list[tuple[Client, "topology.EdgeSpec"]] = []
    for edge in runner.edges:
        bd_seq = runner.bd_seq(edge.edge_id)
        will = build_ndeath_will(GROUP_ID, edge.edge_id, bd_seq=bd_seq)
        client = Client(
            hostname=cfg.mqtt_host,
            port=cfg.mqtt_port,
            identifier=f"sim-{edge.edge_id}",
            protocol=ProtocolVersion.V311,
            will=will,
            clean_session=True,
        )
        edge_clients.append((client, edge))

    # Open all clients concurrently inside a TaskGroup. When the TaskGroup exits
    # (any task raises), all clients' async-with blocks release together.
    async with asyncio.TaskGroup() as tg:
        for client, edge in edge_clients:
            tg.create_task(_run_edge_session(client, edge, runner))


async def _run_edge_session(client: Client, edge, runner: ScenarioRunner) -> None:
    """Open one aiomqtt client and run the scenario for one edge."""
    async with client:
        logger.info("connected edge=%s id=sim-%s", edge.edge_id, edge.edge_id)
        await runner.run_edge(client, edge)


async def main() -> None:
    cfg = get_config()
    logger.info(
        "sparkplug_sim starting — NATS=%s MQTT=%s heartbeat=%.1fs scenario_start_offset=%.1fs",
        cfg.nats_url, cfg.mqtt_url, cfg.sim_heartbeat_interval_sec, cfg.scenario_start_offset_sec,
    )

    # Per RESEARCH Pitfall 5: NATS BEFORE heartbeat.
    await nats_client.connect(cfg.nats_url)

    hb_task = asyncio.create_task(
        heartbeat_loop("sim", interval_sec=cfg.sim_heartbeat_interval_sec)
    )

    # Publish retained host STATE before any per-edge session starts. Survives
    # the per-edge reconnect loop because the broker keeps the retained value
    # independent of this client's session lifetime.
    await _publish_host_state(cfg)

    # Load and validate scenario.yaml (per ADR-0007 Amendment 2026-04-29).
    # Validation failures raise before any NBIRTH is published.
    params = load_scenario_params(cfg.sim_scenario_path)
    runner = ScenarioRunner(
        params=params,
        scenario_start_offset_sec=cfg.scenario_start_offset_sec,
    )
    try:
        # Outer reconnect loop. Per ADR-0007: each disconnect bumps bd_seq for
        # the affected edges; the t=5:00 cue (alias renumbering on edge2) is
        # signalled by setting reorder_for_next_birth before reconnect.
        cancelled = False
        while not cancelled:
            try:
                await _run_one_session(cfg, runner)
            except* MqttError as eg:  # asyncio.TaskGroup wraps in ExceptionGroup
                logger.warning("MQTT error in session: %s — reconnecting in %ds",
                               eg.exceptions[0] if eg.exceptions else eg, _RECONNECT_INTERVAL_SEC)
                # Bump bd_seq on every reconnect so a fresh-NBIRTH is issued.
                for edge in runner.edges:
                    runner._bd_seq[edge.edge_id] += 1
                # Cue alias renumbering for edge2 on the next NBIRTH (ADR-0007 t=5:00).
                # In v1 we do this on EVERY reconnect for edge2 — the demo's kill-and-
                # restart at 4:45 is the natural trigger.
                runner.request_reorder_for_next_birth("edge2")
                await asyncio.sleep(_RECONNECT_INTERVAL_SEC)
            except* asyncio.CancelledError:
                # PEP 654 forbids break/continue/return inside except*.
                cancelled = True
    except asyncio.CancelledError:
        pass
    finally:
        hb_task.cancel()
        try:
            await hb_task
        except asyncio.CancelledError:
            pass
        await nats_client.drain()
        logger.info("sparkplug_sim stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
