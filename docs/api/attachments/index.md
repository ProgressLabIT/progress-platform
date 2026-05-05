---
title: Attachments — API Reference
description: Attachments API operations — Progress Platform.
---

# Attachments API

Media objects and file management — upload, update, retrieve, and delete.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /media/create](/api/attachments/post-media/create) — Create a new media object.
- [GET /media/{media_key}](/api/attachments/get-media/media-key) — Fetch a media object.
- [PATCH /media/{media_key}](/api/attachments/patch-media/media-key) — Update a media object.
- [DELETE /media/{media_key}](/api/attachments/delete-media/media-key) — Delete a media object.
- [POST /files](/api/attachments/post-files) — Upload one or more files.
- [DELETE /files](/api/attachments/delete-files) — Delete one or more files.
