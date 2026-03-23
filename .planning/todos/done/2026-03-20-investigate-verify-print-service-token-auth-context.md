---
created: 2026-03-20T23:06:16.419Z
title: Investigate verify_print_service_token USER_SESSION auth context
area: api
files:
  - backend/api/utils/auth.py
  - backend/print-service/main.py
---

## Problem

`verify_print_service_token` in `auth.py` checks `token_data.context != TokenContext.USER_SESSION` — but service accounts would typically get a different context (e.g. `TokenContext.API`). The print service authenticates via OAuth2 password grant to `/api/auth` using a dedicated service username/password.

If the `/api/auth` endpoint issues a `USER_SESSION` context token to the print service user (because that's the only grant type), the check works but is semantically wrong. If a future change separates service account token contexts, the print service will silently stop being able to authenticate.

## Solution

1. Verify manually that `POST /api/auth` with print service credentials returns a token with `context = USER_SESSION` and `scope` containing `print_service`.
2. If it does: add a comment documenting this intentional choice.
3. If not: fix the guard to use the appropriate context constant for service accounts.

Check `backend/api/endpoints/auth.py` for how token context is assigned during password grant.
