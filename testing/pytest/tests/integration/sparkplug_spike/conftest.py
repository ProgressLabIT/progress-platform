"""Spike pytest fixtures.

Per CONTEXT.md D-07, these tests run against an ALREADY-DEPLOYED docker stack
(no in-process FastAPI; no testcontainers ArangoDB). The fixtures here connect
to localhost:1883 (MQTT) and the local Docker daemon, NOT to an in-process app.

Per RESEARCH §Open Question #3, container-name resolution under Docker Swarm
is non-trivial — the helper `_resolve_container_for_service` resolves a Swarm
service name (e.g. `progress_sparkplug_sim`) into the actual container ID of
the running task.
"""
import asyncio
import logging
from typing import AsyncIterator

import aiomqtt
import docker
import pytest

logger = logging.getLogger("sparkplug_spike")

# All tests in this directory require an integration deployment.
pytestmark = pytest.mark.integration

MQTT_HOST = "localhost"
MQTT_PORT = 1883


@pytest.fixture
def docker_client():
    """A Docker SDK client connected to the local daemon."""
    client = docker.from_env()
    yield client
    client.close()


def _resolve_container_for_service(client, service_name: str) -> "docker.models.containers.Container":
    """Resolve a Swarm service name to its running task's container.

    Per RESEARCH Assumption A7 / Open Question #3: under `docker stack deploy`,
    container names are like `progress_sparkplug_sim.<replica>.<task_id>` —
    the bare service name is NOT a container name.

    Strategy:
      1. Try `client.services.get(service_name)`. If it returns a Service,
         walk its tasks and find the one with state="running".
      2. Fallback: iterate `client.containers.list()` and find a container
         whose name starts with `service_name` and ends with a task ID.
    """
    # Try the Swarm path first.
    try:
        svc = client.services.get(service_name)
        for task in svc.tasks(filters={"desired-state": "running"}):
            container_id = task.get("Status", {}).get("ContainerStatus", {}).get("ContainerID")
            if container_id:
                return client.containers.get(container_id)
    except docker.errors.NotFound:
        pass
    except Exception as e:  # noqa: BLE001 — fall through to the prefix match
        logger.debug("services.get(%s) failed: %s — trying prefix match", service_name, e)
    # Fallback: prefix match on the running container list.
    for c in client.containers.list():
        if c.name.startswith(service_name + "."):
            return c
        if c.name == service_name:  # plain `docker compose up` deployments
            return c
    raise RuntimeError(f"could not resolve a running container for service {service_name!r}")


@pytest.fixture
def resolve_container(docker_client):
    """Returns a function (service_name) -> Container."""
    def _resolve(service_name: str):
        return _resolve_container_for_service(docker_client, service_name)
    return _resolve


@pytest.fixture
async def mqtt_subscriber() -> AsyncIterator[list[tuple[str, bytes]]]:
    """Open an aiomqtt subscriber to spBv1.0/+/NDEATH/+ and record arrivals.

    Yields the live-growing list of (topic, payload) tuples.
    Cancels the collector task on teardown.
    """
    received: list[tuple[str, bytes]] = []
    client = aiomqtt.Client(
        hostname=MQTT_HOST, port=MQTT_PORT,
        identifier="spike-subscriber-ndeath",
        protocol=aiomqtt.ProtocolVersion.V311,
    )
    async with client:
        await client.subscribe("spBv1.0/+/NDEATH/+", qos=1)

        async def _collect():
            async for m in client.messages:
                received.append((m.topic.value, m.payload))

        task = asyncio.create_task(_collect())
        try:
            yield received
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


@pytest.fixture
async def mqtt_state_subscriber() -> AsyncIterator[list[tuple[str, bytes]]]:
    """Fresh-subscriber connecting AFTER the simulator has published retained STATE.

    Used by test_retained_state_qos1.
    """
    received: list[tuple[str, bytes]] = []
    client = aiomqtt.Client(
        hostname=MQTT_HOST, port=MQTT_PORT,
        identifier="spike-fresh-subscriber-state",
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=True,
    )
    async with client:
        await client.subscribe("spBv1.0/STATE/#", qos=1)
        try:
            # Take the first message that arrives within 2s.
            msg = await asyncio.wait_for(anext(client.messages), timeout=2.0)
            received.append((msg.topic.value, msg.payload))
        except asyncio.TimeoutError:
            pass
        yield received
