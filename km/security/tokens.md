# Tokens (Authentication)

Tokens in the Progress Platform are JWT access tokens backed by server-side records in the `Token` collection. This allows validation, revocation, and binding to a specific token instance (e.g. single active session per user).

## Overview

- **Session tokens**: Issued at login (`POST /api/auth`). Tied to a `UserSession`, fixed lifetime (e.g. 24 h). **Only one active session per user** — see below.
- **API tokens**: Manually created in Settings → API Token Library (`GET /api-token`). Long-lived, user-chosen expiration and description, no session binding. Used for scripts and integrations.
- **SSE tickets**: Short-lived (90 s), topic-scoped, stateless JWTs used exclusively to authenticate SSE stream subscriptions. See below.

Session and API tokens use the same mechanism: JWT signed with HS256 + a `Token` document (key, signature, revoked, context, etc.). SSE tickets are stateless — no `Token` DB record is written.

## Token lifecycle

### Single active session per user (session tokens)

When you obtain a session token through the auth endpoint (`POST /api/auth`), every other existing session for that user is terminated first.

Flow: after validating username/password, the backend looks up all active `UserSession` records for that user (`user_key=user.key`, `active=True`). For each one it calls `auth.close_session(session_key, token_key)`, which marks the session inactive and revokes the associated token. Only then is a new session token issued. So at any time a user has at most one active session; a new login invalidates any previous session (e.g. another browser or device). API tokens are unaffected — only sessions (context `USER_SESSION`) are closed.

Implementation: `backend/api/endpoints/auth.py` (lines 57–65), before issuing the new token.

### Issuing

- **Session**: `auth.issue_token(consumer_key=user.key, scope=user.scope, seconds_until_expired=ACCESS_TOKEN_EXPIRE_MINUTES*60)` with `TokenContext.USER_SESSION`. A `TokenRecord` is stored with `context=USER_SESSION` and the JWT’s signature segment. Response includes `access_token` (JWT) and `action='start_session'` or `'reset_password'`.
- **API**: User is already logged in. `GET /api-token?token_description=...&token_expiration=...` calls `auth.issue_token(consumer_key=user_token.consumer_key, expiration_date=token_expiration, scope=user.scope)` with `TokenContext.API`. A `TokenRecord` is stored with `context=API`, `description=token_description`, and the JWT’s signature. Response includes `access_token` (JWT). The token is shown once in the UI (copy to clipboard).

### Verification (protected routes)

- Client sends `Authorization: Bearer <JWT>`.
- `auth.verify_token` (FastAPI dependency):
  1. Decode JWT with `TOKEN_SECRET` and `ALGORITHM` (HS256); reject if invalid or expired.
  2. Build `TokenData` from payload; load `TokenRecord` from `Token` by `token_key` (JWT `jti`).
  3. Reject if record missing, or if the token string’s signature segment ≠ `token_record.signature`, or if `token_record.revoked`.
- Returns `TokenData` (e.g. `consumer_key`, `context`, `scope`) for the route.

### Revocation

- **Revoke a token**: `auth.revoke_token(token_key)` sets `revoked=True` on the `Token` document. Subsequent `verify_token` calls for that JWT return 401.
- **Session**: Closing a session (`DELETE /api/session/{session_key}` or logout) calls `auth.close_session(session_key, token_key)`, which marks the `UserSession` inactive and revokes the associated token.
- **API token**: User deletes the token in API Token Library → `DELETE /api-token/{token_key}` → `auth.revoke_token(token)`.

## Data model

- **JWT payload** (`TokenData`): `jti` (token_key), `sub` (consumer_key), `ctyp` (consumer_type), `ctx` (context), `iat`, `exp`, and optionally `scope`. Same structure for session and API tokens; `context` distinguishes use.
- **Token collection** (`TokenRecord`): `key` (= token_key), `issued_to`, `issued_at`, `expires_at`, `context`, `signature` (JWT’s last segment), `revoked`, and for API tokens `description`. Used to validate and revoke.

## Constants (reference)

| Constant | Value | Use |
|----------|--------|-----|
| `ACCESS_TOKEN_EXPIRE_MINUTES` (auth) | 1440 (24 h) | Session token lifetime |
| `RESET_PASSWORD_TOKEN_EXPIRE_MINUTES` | 5 | Password-reset token |
| `USER_SESSION_TIMEOUT_MINUTES` | 15 | Session timeout (e.g. UI) |
| API token expiration | User-chosen date | From API Token Library form |

## SSE tickets

Browser `EventSource` cannot set request headers, so a short-lived ticket is used instead of passing the long-lived JWT as a URL parameter.

**Flow:**
1. Client calls `POST /api/notification/ticket` with `Authorization: Bearer <session JWT>` and body `{"topic": "<topic>"}`.
2. Backend validates the session JWT, enforces user-topic owner match for `user:<key>` topics, and returns `{"ticket": "<short JWT>", "expires_in": 90}`.
3. Client opens `new EventSource("/api/notification/<topic>?ticket=<short JWT>")`.
4. Backend validates the ticket: checks signature, `ctx=sse_ticket`, and `topic` claim matches the path. If valid, the stream opens; otherwise 401.

**Ticket properties:**
- `ctx = sse_ticket` — rejected by `verify_token` so cannot authenticate any other endpoint.
- `topic` claim — must match the path parameter; a ticket for `task` cannot open `production`.
- `sub` claim — bound to the issuing user's `consumer_key`.
- 90 s TTL — within this window native `EventSource` reconnect reuses the same URL/ticket automatically. When the ticket expires and the browser's reconnect fails (CLOSED state), `useSSE` fetches a fresh ticket and reopens.
- Stateless — no `Token` DB write; signature-only validation via `jwt_secret`.

**Security properties vs. long-lived JWT in URL:**
- Leaked ticket (access logs, Referer, history) expires in ≤90 s.
- Usable only on the specific topic it was issued for.
- Cannot be replayed against any API endpoint other than the SSE stream.

**Implementation:** `backend/api/endpoints/notification.py` (`mint_ticket`, `_verify_stream_access`), `backend/api/utils/auth.py` (`issue_sse_ticket`, `verify_sse_ticket`, `SSE_TICKET_TTL_SECONDS`), `webapps/main/src/composables/useSSE.js`.

## Planned: device tokens & consumer-type taxonomy (ADR-0015, discussion)

> Forward-looking — not yet implemented. See [ADR-0015](../decisions/0015-device-consumer-identity-model.md) (status: `discussion`). Today's `ConsumerType` is `{ USER, PROGRESS_APP, EQUIPMENT }`; only `USER` is in live use.

ADR-0015 proposes a non-human **device identity** usable by NFC/biometric readers, kiosks, and IIoT edge nodes, minted from one **Device registry** via the existing NATS enrollment service. What touches this document:

- **`ConsumerType` → `{ PROGRESS, DEVICE, 3PSW, USER }`** (no migration — `PROGRESS_APP`/`EQUIPMENT` have no live references). `PROGRESS` = trusted first-party services + IIoT bridges; `DEVICE` = constrained edge identity; `3PSW` = third-party software (ERP, external plugins); `USER` = humans.
- **Device token** = a `ConsumerType.DEVICE` Progress-API JWT (HS256 + `Token` record, same mechanism as today) with a **flat `scope`**. NATS pub/sub permissions live in the *separate* NATS user JWT (`nats-nkey-auth.md`), never here — identity is unified at the registry, enforcement stays per-plane.
- **Two-layer sessions:** a long-lived **device session** (the kiosk/station; holds the SSE channel; the trust anchor) + a short-lived **operator session** overlay (who is at the station now). The backend holds the `station ↔ operator` binding, so a browser refresh recovers the operator session.
- **Device ≠ Asset:** `DEVICE` is an auth/identity type; `Asset`/`AssetClass` is the OT domain model. Related, not equal — the registry links a Device to an Asset only when one exists.

## Related

- **Endpoints**: `backend/api/endpoints/auth.py` (login, session, whoami), `backend/api/endpoints/org.py` (api-token, user/api-tokens), `backend/api/endpoints/notification.py` (SSE ticket issuance, SSE stream).
- **Utils**: `backend/api/utils/auth.py` (`issue_token`, `verify_token`, `revoke_token`, `close_session`, `issue_sse_ticket`, `verify_sse_ticket`).
- **Models**: `backend/api/models/auth.py` (`TokenData`, `TokenRecord`, `TokenContext`, `SseTicketClaims`, `ConsumerType`).
- **UI**: `webapps/main/src/components/settings/APITokenLibrary.vue`, `webapps/main/src/views/settings/APITokenSettings.vue`, `webapps/main/src/composables/useSSE.js`.
