# Tokens (Authentication)

Tokens in the Progress Platform are JWT access tokens backed by server-side records in the `Token` collection. This allows validation, revocation, and binding to a specific token instance (e.g. single active session per user).

## Overview

- **Session tokens**: Issued at login (`POST /api/auth`). Tied to a `UserSession`, fixed lifetime (e.g. 24 h). **Only one active session per user** — see below.
- **API tokens**: Manually created in Settings → API Token Library (`GET /api-token`). Long-lived, user-chosen expiration and description, no session binding. Used for scripts and integrations.

Both use the same mechanism: JWT signed with HS256 + a `Token` document (key, signature, revoked, context, etc.).

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

## Related

- **Endpoints**: `backend/api/endpoints/auth.py` (login, session, whoami), `backend/api/endpoints/org.py` (api-token, user/api-tokens).
- **Utils**: `backend/api/utils/auth.py` (`issue_token`, `verify_token`, `revoke_token`, `close_session`).
- **Models**: `backend/api/models/auth.py` (`TokenData`, `TokenRecord`, `TokenContext`, `ConsumerType`).
- **UI**: `webapps/main/src/components/settings/APITokenLibrary.vue`, `webapps/main/src/views/settings/APITokenSettings.vue`.
