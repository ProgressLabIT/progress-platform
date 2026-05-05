---
title: Quality — API Reference
description: Quality API operations — Progress Platform.
---

# Quality API

Quality form fields, custom lists, print templates, and print job execution.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [POST /field](/api/quality/post-field) — Create a form field definition.
- [GET /field](/api/quality/get-field) — Fetch form field definitions.
- [PUT /field/{field_key}](/api/quality/put-field/field-key) — Replace a form field definition.
- [DELETE /field/{field_key}](/api/quality/delete-field/field-key) — Delete a form field definition.
- [GET /list](/api/quality/get-list) — Fetch custom list values for a field.
- [POST /list/{field_key}](/api/quality/post-list/field-key) — Create or update custom list values.
- [DELETE /list/{field_key}](/api/quality/delete-list/field-key) — Delete custom list values.
- [GET /print-template](/api/quality/get-print-template) — Find print templates.
- [GET /print-template/{template_key}](/api/quality/get-print-template/template-key) — Get print template details.
- [POST /print-template](/api/quality/post-print-template) — Create a print template.
- [PUT /print-template](/api/quality/put-print-template) — Update a print template.
- [DELETE /print-template/{template_key}](/api/quality/delete-print-template/template-key) — Delete a print template.
- [POST /update-template-assignments](/api/quality/post-update-template-assignments) — Update print template assignments.
- [POST /print-job](/api/quality/post-print-job) — Execute a print job using a template.
