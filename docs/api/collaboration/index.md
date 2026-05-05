---
title: Collaboration — API Reference
description: Collaboration API operations — Progress Platform.
---

# Collaboration API

Issues, issue types, messages, tasks, and task types.

> Operations below are scaffolded from FastAPI introspection. Each operation page
> renders inline via `<OAOperation>` once CI populates `openapi.json`.

## Operations

- [GET /issue-type](/api/collaboration/get-issue-type) — List issue types.
- [POST /issue-type](/api/collaboration/post-issue-type) — Create a new issue type.
- [PATCH /issue-type/{issue_type_key}](/api/collaboration/patch-issue-type/issue-type-key) — Update an issue type.
- [DELETE /issue-type/{issue_type_key}](/api/collaboration/delete-issue-type/issue-type-key) — Delete an issue type.
- [GET /issue](/api/collaboration/get-issue) — Search issues.
- [GET /message](/api/collaboration/get-message) — Fetch messages.
- [GET /task](/api/collaboration/get-task) — Search tasks.
- [GET /task/{task_key}](/api/collaboration/get-task/task-key) — Fetch task data.
- [GET /task-type](/api/collaboration/get-task-type) — List task types.
- [POST /task-type](/api/collaboration/post-task-type) — Create a task type.
- [PUT /task-type/{type_key}](/api/collaboration/put-task-type/type-key) — Update a task type.
- [DELETE /task-type/{type_key}](/api/collaboration/delete-task-type/type-key) — Delete a task type.
