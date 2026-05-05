---
title: Security — API Reference
description: Security API operations — Progress Platform.
---

# Security API

Authentication, session management, and password operations.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /auth](/api/security/post-auth) — Authenticate a user and issue a bearer token.
- [POST /user/{user_key}/verify](/api/security/post-user/user-key/verify) — Verify a user's current password.
- [GET /whoami](/api/security/get-whoami) — Return the user key from the current session token.
- [POST /session](/api/security/post-session) — Open a new user session after token issuance.
- [DELETE /session/{session_key}](/api/security/delete-session/session-key) — Close an active user session and revoke its token.
