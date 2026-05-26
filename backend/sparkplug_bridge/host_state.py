"""Primary-host STATE handshake state for the sparkplug bridge.

Per CONTEXT.md D-02/D-03/D-04 + RESEARCH §2:
  - bridge publishes spBv1.0/STATE/<host_id> ONLINE retained on startup
  - bridge attaches LWT spBv1.0/STATE/<host_id> = b"OFFLINE" retained
  - bridge subscribes to its own STATE topic; flips state_online = True
    ONLY after the broker echoes ONLINE back (round-trip observed; D-03)

The HostState dataclass is the single shared mutable object that the
subscriber, heartbeat, and main.py all read/write. It exists so the
heartbeat task can publish current bool values at every tick without
main.py having to push them in via parameters or globals.

Lifecycle:
  - main.py instantiates HostState() once at startup
  - subscriber.py flips mqtt_connected on async-with-client enter/exit
  - main.py flips nats_connected after nats_client.connect succeeds
  - handle_state_echo flips state_online when the STATE loopback echo arrives
  - main.py updates active_session_count whenever a session starts/ends
  - heartbeat.py reads all four every tick (Plan 02-06 wires this)
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger("sparkplug_bridge.host_state")

# Wire payloads — bytes per aiomqtt convention, matched to the literal
# strings the bridge publishes and the broker echoes back via retained.
ONLINE_PAYLOAD = b"ONLINE"
OFFLINE_PAYLOAD = b"OFFLINE"


@dataclass
class HostState:
    """Mutable shared state for the bridge's runtime health surface (D-02).

    Values feed both the heartbeat enrichment payload and the STATE
    handshake. Heartbeat reads these every interval_sec tick.
    """

    mqtt_connected: bool = False
    nats_connected: bool = False
    state_online: bool = False
    active_session_count: int = 0


def handle_state_echo(
    state: HostState,
    host_id: str,
    payload: bytes,
    *,
    expected_host_id: str,
) -> None:
    """Process a received STATE message on the loopback subscription.

    Args:
        state: the shared HostState instance (mutated in place).
        host_id: the host_id parsed from the STATE topic
                 (`spBv1.0/STATE/<host_id>` -> `<host_id>`).
        payload: raw MQTT payload bytes (b"ONLINE" or b"OFFLINE").
        expected_host_id: the bridge's own host id from cfg.bridge_host_id;
                          echoes from OTHER host ids are ignored (the bridge
                          may receive STATE from other primary hosts on the
                          same broker — those are not its echo).

    Per D-03: state_online flips true ONLY when the broker echoes our own
    retained ONLINE back. An OFFLINE echo (e.g. from a previous LWT) flips
    state_online false to be conservative, but that is rare in practice
    because the bridge re-publishes ONLINE retained on every reconnect
    (subscriber.py).
    """
    if host_id != expected_host_id:
        logger.debug(
            "ignoring STATE echo for foreign host_id=%s (we are %s)",
            host_id,
            expected_host_id,
        )
        return

    if payload == ONLINE_PAYLOAD:
        if not state.state_online:
            logger.info(
                "state_online flipped True (round-trip observed for %s)", host_id
            )
        state.state_online = True
    elif payload == OFFLINE_PAYLOAD:
        if state.state_online:
            logger.warning(
                "state_online flipped False (received OFFLINE echo for %s)", host_id
            )
        state.state_online = False
    else:
        logger.warning(
            "unexpected STATE payload for %s: %r — ignoring (state_online unchanged)",
            host_id,
            payload[:64],
        )
