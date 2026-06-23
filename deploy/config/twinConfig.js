/**
 * LIVE runtime config for the Aerospace Mill Live Twin HMI panel.
 *
 * On the server this file lives at /opt/progress/config/twinConfig.js and is
 * mounted by mill-twin.yaml directly OVER the image's static/config.js — the
 * same pattern the main app uses for appConfig.js (stack.yaml). It is served
 * verbatim as /twin/config.js; it is NOT merged with anything.
 *
 * To change WO links / NATS URL: edit this file, then
 *   docker service update --force progress_demo_twin
 * No image rebuild. (In-place edits reflect on reload; an editor that replaces
 * the file needs the force-update above to re-point the bind mount.)
 *
 * The image's baked backend/demo_twin/static/config.js is the fallback used only
 * when this file is not mounted (e.g. local dev without the config volume).
 */

// NATS WebSocket URL.
//   https (server): wss://<page-host>/nats — the Traefik `natsws` route
//                   (nats-ws.yaml) forwards /nats → broker:8090.
//   http  (local) : ws://localhost:8090 (dev.yaml publishes the broker WS).
// Set an explicit string to override the derivation.
window.NATS_WS_URL = window.NATS_WS_URL || (
  location.protocol === 'https:'
    ? `wss://${location.host}/nats`
    : 'ws://localhost:8090'
);

// HTTP command base for /setpoints, /fault, /reset.
//   https (server): '/twin' — the panel is served under Traefik's PathPrefix(`/twin`);
//                   a root-relative '/setpoints' misses that router and returns 405.
//   http  (local) : '' — demo_twin is served at the root (http://localhost:8001/).
// Set an explicit string to override (e.g. 'http://localhost:8001' for file:// dev).
window.DEMO_TWIN_BASE_URL = window.DEMO_TWIN_BASE_URL || (
  location.protocol === 'https:' ? '/twin' : ''
);

// Work-order link keys the Phase-3 Issue automation attaches the Issue to.
// EDIT THESE to retarget the demo WO — keep them in sync with the matching keys
// in /opt/progress/config/mill_automation.json.
window.WO_LINKS = window.WO_LINKS || {
  serial:     'WING-DEMO-001',
  work_order: 'WO-DEMO-001',
  operation:  'OP-DEMO-001',
};
