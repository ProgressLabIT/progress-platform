---
title: Organization — API Reference
description: Organization API operations — Progress Platform.
---

# Organization API

Users, departments, API tokens, and org-level access management.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /department](/api/organization/get-department) — List all departments.
- [GET /api-token](/api/organization/get-api-token) — List API tokens.
- [DELETE /api-token/{token_key}](/api/organization/delete-api-token/token-key) — Revoke an API token.
- [GET /user](/api/organization/get-user) — List all users.
- [POST /user](/api/organization/post-user) — Create a new user.
- [PATCH /user/{user_key}](/api/organization/patch-user/user-key) — Update a user record.
- [PUT /user/{user_key}/image](/api/organization/put-user/user-key/image) — Update a user profile image.
- [DELETE /user/{user_key}/password](/api/organization/delete-user/user-key/password) — Delete a user password (force reset on next login).
- [PUT /user/{user_key}/password](/api/organization/put-user/user-key/password) — Reset a user password.
- [GET /user/api-tokens](/api/organization/get-user/api-tokens) — List API tokens for a user.
- [DELETE /user/{user_key}](/api/organization/delete-user/user-key) — Archive (soft-delete) a user.
