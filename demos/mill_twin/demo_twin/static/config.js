/**
 * Runtime configuration for the Aerospace Mill Live Twin HMI.
 *
 * All constants are set on `window` so they can be overridden by the
 * host environment before this script loads (Phase-5 deployment pattern).
 *
 * NATS_WS_URL: WebSocket URL for the NATS broker.
 *   - On HTTPS (the deployed server): derived as wss://<page-host>/nats — the
 *     Traefik `natsws` route the server exposes (PathPrefix(`/nats`) → broker:8090).
 *     Must be wss:// (a plain ws:// from an https page is blocked as mixed content)
 *     and must NOT be localhost (that's the viewer's machine, not the server).
 *   - On HTTP (local dev): falls back to ws://localhost:8090 (dev.yaml publishes 8090).
 *   - Override explicitly via window.NATS_WS_URL = '...' BEFORE this script loads.
 *
 * DEMO_TWIN_BASE_URL: Base URL for HTTP command endpoints (/setpoints, /fault, /reset).
 *   - '' (empty string) = same-origin when served by demo_twin at http://localhost:8001/
 *   - Set to 'http://localhost:8001' for file:// dev mode so fetch() uses the absolute URL
 *   - Override via window.DEMO_TWIN_BASE_URL = '...' BEFORE this script loads
 *
 * WO_LINKS: Work-order link keys used by the Phase-3 Issue automation.
 *   The visual ticket strings ("WO-A350-SPAR-0488", "SPAR-OUTBD-R12") are the
 *   display mocks. These keys are what the automation uses to link the Issue to
 *   the actual Progress objects (serial / work_order / operation).
 *   Phase 5 overrides these with real config values from MILL_AUTO_LINKED_* env.
 */

window.NATS_WS_URL = window.NATS_WS_URL || (
  location.protocol === 'https:'
    ? `wss://${location.host}/nats`   // server: Traefik natsws route → broker:8090
    : 'ws://localhost:8090'           // local dev: dev.yaml publishes broker WS on 8090
);

// https (server): '/twin' — panel served under Traefik PathPrefix(`/twin`); a root
// '/setpoints' misses that router → 405. http (local): '' — demo_twin served at root.
window.DEMO_TWIN_BASE_URL = window.DEMO_TWIN_BASE_URL || (
  location.protocol === 'https:' ? '/twin' : ''
);

// D-08: link keys wired to Phase-3 automation MILL_AUTO_LINKED_* defaults.
// Visual ticket copy ("WO-A350-SPAR-0488") is the display string; these are the IDs.
window.WO_LINKS = window.WO_LINKS || {
  serial:     'WING-DEMO-001',
  work_order: 'WO-DEMO-001',
  operation:  'OP-DEMO-001',
};
