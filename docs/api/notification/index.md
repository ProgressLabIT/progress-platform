---
title: Notification — API Reference
description: Notification API operations — Progress Platform.
---

# Notification API

Server-Sent Events stream and notification ticket minting.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /notification/ticket](/api/notification/post-notification/ticket) — Mint a short-lived SSE subscription ticket.
- [GET /notification/{topic}](/api/notification/get-notification/topic) — Subscribe to a Server-Sent Events notification stream.
