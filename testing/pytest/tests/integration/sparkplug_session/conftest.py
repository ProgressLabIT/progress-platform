"""Phase 2 integration test fixtures.

Per CONTEXT.md D-13/D-14/D-15:
  - Tests run against an ALREADY-DEPLOYED docker stack (broker on
    localhost:1883 MQTT and localhost:4222 NATS). The ``nats_fixture`` is
    session-scoped; ``fresh_kv_buckets`` resets the four sparkplug_* buckets
    between tests via delete_key_value + create_key_value.
  - Assertions land on NATS subjects + KV reads, NOT on bridge internals.
  - The simulator is NOT extended; pathological frames are built in
    frames.py and published via the ``mqtt_publisher`` fixture.
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import AsyncIterator

import aiomqtt
import docker
import nats
import nats.js.api
import nats.js.errors
import pytest

# ---------------------------------------------------------------------------
# Path bootstrap — allow ``from backend.sparkplug import sparkplug_b_pb2``
# and ``from sparkplug_bridge.kv_store import BUCKET_*`` from any test in
# this directory.  The conftest is at depth 5 below the repo root:
#   testing/pytest/tests/integration/sparkplug_session/conftest.py
#                                                      [0]
#                                               [1]
#                                       [2]
#                                [3]
#                         [4]
#   [5] = repo root
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[5]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# KV bucket name constants — imported from the bridge module so a rename
# propagates automatically to all tests.
from sparkplug_bridge.kv_store import (  # noqa: E402
    BUCKET_ALIASES,
    BUCKET_LAST_SEQ,
    BUCKET_LAST_VALUES,
    BUCKET_SESSIONS,
)

logger = logging.getLogger("sparkplug_session")

# All tests in this directory require an integration deployment.
pytestmark = pytest.mark.integration

MQTT_HOST = "localhost"
MQTT_PORT = 1883
NATS_URL = "nats://localhost:4222"

_ALL_SPARKPLUG_BUCKETS = (
    BUCKET_SESSIONS,
    BUCKET_ALIASES,
    BUCKET_LAST_SEQ,
    BUCKET_LAST_VALUES,
)


# ---------------------------------------------------------------------------
# Docker fixtures — copied from Phase 1 spike conftest so sparkplug_session/
# tests are self-contained.
# ---------------------------------------------------------------------------

@pytest.fixture
def docker_client():
    """A Docker SDK client connected to the local daemon."""
    client = docker.from_env()
    yield client
    client.close()


def _resolve_container_for_service(client, service_name: str):
    """Resolve a Swarm service name to its running task's container.

    Mirrors the Phase 1 spike conftest implementation.  Under
    ``docker stack deploy`` container names look like:
    ``<service>.<replica>.<task_id>`` — the bare service name is not a
    container name.

    Strategy:
      1. Try ``client.services.get(service_name)`` (Swarm path).
      2. Fallback: prefix-match ``client.containers.list()``.
    """
    try:
        svc = client.services.get(service_name)
        for task in svc.tasks(filters={"desired-state": "running"}):
            container_id = task.get("Status", {}).get("ContainerStatus", {}).get("ContainerID")
            if container_id:
                return client.containers.get(container_id)
    except docker.errors.NotFound:
        pass
    except Exception as e:  # noqa: BLE001
        logger.debug("services.get(%s) failed: %s — trying prefix match", service_name, e)
    for c in client.containers.list():
        # Swarm pattern: <service>.<replica>.<task_id>
        if c.name.startswith(service_name + "."):
            return c
        if c.name == service_name:
            return c
        # Compose pattern: <project>-<service>-<replica> or <project>_<service>_<replica>
        # e.g. progress-sparkplug-validate-broker-1 / progress_broker_1
        if (
            c.name.endswith(f"-{service_name}-1") or c.name.endswith(f"_{service_name}_1")
            or f"-{service_name}-" in c.name or f"_{service_name}_" in c.name
        ):
            return c
    raise RuntimeError(f"could not resolve a running container for service {service_name!r}")


@pytest.fixture
def resolve_container(docker_client):
    """Return a callable ``(service_name: str) -> Container``."""
    def _resolve(service_name: str):
        return _resolve_container_for_service(docker_client, service_name)
    return _resolve


# ---------------------------------------------------------------------------
# NATS connection — function-scoped to match pytest-asyncio's default
# function-scoped event loops. A session-scoped client cached its request
# futures on the original loop; subsequent tests on fresh loops would never
# see those futures resolve, producing nats.errors.TimeoutError on every
# JetStream call. Per RESEARCH §6 the localhost reconnect cost is negligible
# (~10 ms), so per-test connections are simpler than fighting the loop scope.
# ---------------------------------------------------------------------------

@pytest.fixture
async def nats_fixture():
    """Function-scoped raw NATS client.

    A new connection per test keeps the client's request inbox bound to the
    test's event loop, so JetStream KV operations resolve cleanly.
    """
    nc = await nats.connect(NATS_URL)
    try:
        yield nc
    finally:
        await nc.drain()


# ---------------------------------------------------------------------------
# Per-test KV reset (function-scoped) — D-15
# ---------------------------------------------------------------------------

@pytest.fixture
async def fresh_kv_buckets(nats_fixture) -> AsyncIterator[dict]:
    """Delete and recreate all four sparkplug_* KV buckets per test (D-15).

    Yields a dict mapping bucket name to its fresh ``KeyValue`` object.
    Teardown is intentionally empty — the next invocation's setup phase
    deletes and recreates, so stale entries never cross test boundaries.

    Per RESEARCH §6 this adds ~40 ms overhead per test (4 buckets × ~10 ms
    round-trip).  The bridge's ``ensure_buckets`` is idempotent so a running
    bridge container can race with this fixture without causing errors.
    """
    js = nats_fixture.jetstream()
    result: dict = {}
    for name in _ALL_SPARKPLUG_BUCKETS:
        try:
            await js.delete_key_value(name)
        except nats.js.errors.NotFoundError:
            pass
        except nats.js.errors.APIError as e:
            logger.debug(
                "delete_key_value(%s) APIError (treated as benign): %s", name, e
            )
        kv = await js.create_key_value(nats.js.api.KeyValueConfig(bucket=name, history=1))
        result[name] = kv
    yield result
    # Teardown intentionally empty — next fixture invocation recreates.


# ---------------------------------------------------------------------------
# NATS subscriber for black-box assertion (function-scoped) — D-14
# ---------------------------------------------------------------------------

@pytest.fixture
async def nats_subscriber(nats_fixture) -> AsyncIterator[list[dict]]:
    """Subscribe to progress.sparkplug.> AND progress.notification.sparkplug.

    Yields a live-growing list of dicts:
      {"subject": str, "kind": str | None, "payload": dict | None, "raw": bytes}

    Each message's body is auto-decoded from JSON.  Messages with non-JSON
    bodies yield ``payload=None, kind=None`` so tests can still inspect
    ``raw``.

    Tests filter by ``kind`` (e.g. ``"session.suspect"``) or by ``subject``
    prefix (e.g. ``progress.sparkplug.plant1.edge1``).
    """
    received: list[dict] = []

    async def _cb(msg):
        entry: dict = {"subject": msg.subject, "raw": msg.data}
        try:
            doc = json.loads(msg.data)
            entry["payload"] = doc
            entry["kind"] = doc.get("kind")
        except json.JSONDecodeError:
            entry["payload"] = None
            entry["kind"] = None
        received.append(entry)

    sub_metric = await nats_fixture.subscribe("progress.sparkplug.>", cb=_cb)
    sub_notif = await nats_fixture.subscribe("progress.notification.sparkplug", cb=_cb)
    try:
        yield received
    finally:
        await sub_metric.unsubscribe()
        await sub_notif.unsubscribe()


# ---------------------------------------------------------------------------
# MQTT publisher for injecting handcrafted frames (function-scoped) — D-13
# ---------------------------------------------------------------------------

@pytest.fixture
async def mqtt_publisher() -> AsyncIterator:
    """An aiomqtt client that the test uses to publish handcrafted Sparkplug frames.

    Yields a coroutine ``publish(topic, payload, qos=1, retain=False)``
    that publishes bytes via the connected aiomqtt client.  The client
    lifecycle (connect / disconnect) is managed by this fixture.

    Using ``clean_session=True`` ensures no leftover subscriptions from
    previous test runs accumulate on the broker.
    """
    client = aiomqtt.Client(
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        identifier="sparkplug-session-test-publisher",
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=True,
    )
    async with client:
        async def publish(
            topic: str, payload: bytes, qos: int = 1, retain: bool = False
        ) -> None:
            await client.publish(topic, payload=payload, qos=qos, retain=retain)

        yield publish


# ---------------------------------------------------------------------------
# MQTT STATE subscriber (function-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture
async def mqtt_state_subscriber() -> AsyncIterator[list[tuple[str, bytes]]]:
    """Fresh aiomqtt subscriber to spBv1.0/STATE/# — collects retained STATE messages.

    Used by tests that verify the bridge's STATE handshake round-trip
    (D-04).  ``clean_session=True`` guarantees the subscription is fresh
    per test so retained messages are always re-delivered.
    """
    received: list[tuple[str, bytes]] = []
    client = aiomqtt.Client(
        hostname=MQTT_HOST,
        port=MQTT_PORT,
        identifier="sparkplug-session-state-subscriber",
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=True,
    )
    async with client:
        await client.subscribe("spBv1.0/STATE/#", qos=1)

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


# ---------------------------------------------------------------------------
# Bridge heartbeat NATS subscriber (function-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture
async def bridge_heartbeat_subscriber(nats_fixture) -> AsyncIterator[list[dict]]:
    """Collect bridge heartbeat messages from progress.notification.health.sparkplug.bridge.

    Returns a live-growing list of decoded JSON dicts.  Used by tests that
    assert ``state_online=True`` after a successful STATE echo (D-02).
    """
    received: list[dict] = []

    async def _cb(msg):
        try:
            received.append(json.loads(msg.data))
        except json.JSONDecodeError:
            pass

    sub = await nats_fixture.subscribe(
        "progress.notification.health.sparkplug.bridge", cb=_cb
    )
    try:
        yield received
    finally:
        await sub.unsubscribe()
