"""aiomqtt subscribe loop with LWT, STATE handshake, and canonical reconnect pattern.

Source: aiomqtt official docs (https://aiomqtt.bo3hm.com/reconnection.html).
aiomqtt 2.x has NO built-in auto-reconnect; the standard idiom is the
`while True: try: async with client: ... except MqttError: sleep` shape below.

Phase 2 additions (Plan 02-04):
  - aiomqtt Will set to (spBv1.0/STATE/<host_id>, b"OFFLINE", qos=1, retain=True)
    per CONTEXT.md D-03 (primary-host STATE handshake via LWT).
  - Loopback subscription to spBv1.0/STATE/<bridge_host_id> at QoS 1 — subscribed
    BEFORE spBv1.0/# so the retained ONLINE echo is guaranteed delivered.
  - Retained b"ONLINE" published to spBv1.0/STATE/<bridge_host_id> on every connect.
  - state.mqtt_connected toggles True on async-with-client entry, False on MqttError.
  - state.state_online resets False on entry (stale; re-flips True via main.py
    STATE router when the loopback echo arrives — D-03 round-trip).
"""
import asyncio
import logging

import aiomqtt

try:
    from .host_state import OFFLINE_PAYLOAD, ONLINE_PAYLOAD, HostState
except ImportError:
    from host_state import OFFLINE_PAYLOAD, ONLINE_PAYLOAD, HostState  # type: ignore[no-redef]

logger = logging.getLogger("sparkplug_bridge.subscriber")

_RECONNECT_INTERVAL_SEC = 5
_SPARKPLUG_TOPIC_FILTER = "spBv1.0/#"


def _state_topic(host_id: str) -> str:
    """spBv1.0/STATE/<host_id> per Sparkplug B v3.0.0 § 6.4 primary-host topic."""
    return f"spBv1.0/STATE/{host_id}"


async def run_subscribe_loop(cfg, handle_message, state: HostState) -> None:
    """Connect to MQTT with LWT, subscribe to STATE + spBv1.0/#, publish ONLINE retained.

    Args:
        cfg: BridgeSettings instance (provides mqtt_host, mqtt_port, mqtt_client_id,
             bridge_host_id).
        handle_message: async callable taking (topic: str, payload: bytes).
            Errors raised from this callable are caught and logged (one bad
            frame must not kill the bridge — RESEARCH §Project Constraints).
        state: shared HostState instance; mqtt_connected toggled on connect/disconnect.

    Phase 2 additions over Phase 1:
      - aiomqtt Will set to (spBv1.0/STATE/<host_id>, b"OFFLINE", qos=1, retain=True) per D-03
      - Loopback subscription to spBv1.0/STATE/<cfg.bridge_host_id> at QoS 1
      - Retained b"ONLINE" published to spBv1.0/STATE/<cfg.bridge_host_id>
      - state.mqtt_connected flips True on async-with-client entry, False on MqttError
      - state.state_online is NOT flipped here — it flips when the loopback echo arrives,
        which routes through handle_message -> host_state.handle_state_echo (Plan 02-06)

    clean_session=True is UNCHANGED (CONTEXT.md): KV is the session truth,
    not the MQTT broker session.

    Loops forever; reconnects with a 5s sleep on aiomqtt.MqttError.
    """
    will = aiomqtt.Will(
        topic=_state_topic(cfg.bridge_host_id),
        payload=OFFLINE_PAYLOAD,
        qos=1,
        retain=True,
    )
    client = aiomqtt.Client(
        hostname=cfg.mqtt_host,
        port=cfg.mqtt_port,
        identifier=cfg.mqtt_client_id,
        protocol=aiomqtt.ProtocolVersion.V311,
        clean_session=True,  # KV is the session state, not the MQTT broker session.
        will=will,
    )
    while True:
        try:
            async with client:
                state.mqtt_connected = True
                state.state_online = False  # reset; flips True only on echo
                # Subscribe to STATE loopback FIRST so the retained ONLINE we publish
                # below is guaranteed to be delivered (broker stores it, our subscription
                # picks it up).
                await client.subscribe(_state_topic(cfg.bridge_host_id), qos=1)
                await client.subscribe(_SPARKPLUG_TOPIC_FILTER, qos=1)
                logger.info(
                    "subscribed to %s and %s at %s:%d",
                    _state_topic(cfg.bridge_host_id),
                    _SPARKPLUG_TOPIC_FILTER,
                    cfg.mqtt_host,
                    cfg.mqtt_port,
                )
                # Publish ONLINE retained — broker stores it AND echoes it back to our
                # loopback subscription, which flips state.state_online = True via
                # main.py's STATE handler (D-03 round-trip).
                await client.publish(
                    _state_topic(cfg.bridge_host_id),
                    payload=ONLINE_PAYLOAD,
                    qos=1,
                    retain=True,
                )
                logger.info(
                    "published retained ONLINE to %s",
                    _state_topic(cfg.bridge_host_id),
                )

                async for message in client.messages:
                    try:
                        await handle_message(message.topic.value, message.payload)
                    except Exception:
                        logger.exception(
                            "handle_message failed for %s", message.topic.value
                        )
        except aiomqtt.MqttError as e:
            state.mqtt_connected = False
            state.state_online = False
            logger.warning(
                "MQTT connection error: %s — reconnecting in %ds",
                e,
                _RECONNECT_INTERVAL_SEC,
            )
            await asyncio.sleep(_RECONNECT_INTERVAL_SEC)
