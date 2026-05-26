# Milestone 0.10.0 — GitLab Status Update

**Project:** [`progresslab/progress-platform`](https://gitlab.com/progresslab/progress-platform)
**Milestone:** [0.10.0 (iid 11)](https://gitlab.com/progresslab/progress-platform/-/milestones/11)
**Audited against:** branch `DEV` (post-commit `642e7711`)

After auditing the live `DEV` branch against each open issue, GitLab was reconciled:

- **12 closed** (10 just verified + 2 already closed)
- **11 still open** — 6 partially done (now labelled `STATUS:: Working On`) and 5 untouched

---

## Closed (12)

Each closing comment on GitLab includes anchoring `file:line` evidence and the closing commit hashes.

| # | Title | Closing commits |
|---|---|---|
| #723 | Setup api and events | 4b1d9df4, fcb7abda |
| #724 | Create TaskType configuration screen | 2eaf8a4b, 427665b8 |
| #725 | Create Task detail screen | c427944a, 59330ad2, 01fb65ad |
| #728 | Add task type and task routes | 52185f07, 26f308df |
| #729 | Update issue/serial history to add event source links | *(prior)* |
| #730 | Add task counter config | **d7637978**, 642e7711 |
| #731 | Update User menu to include tasks and use drawer | e6701fdf |
| #733 | Add task management options | 086fea3a, ee760b05 |
| #735 | Auto detect entity task link | 26f308df, 9ce34a6f |
| #759 | Create "adjustment" type movement lists after confirmation | *(prior)* |
| #800 | Implement App Home (UserHome) | e6701fdf |
| #806 | Allow copying PrintTemplates | 427665b8 |

---

## Still open — partial (6, `STATUS:: Working On`)

Issues with substantial implementation but a clearly identified residual gap.

| # | Title | Done | Residual gap |
|---|---|---|---|
| #727 | Create TaskOverview screen | table, multiselect, late icon, status context-menu, status/text/type filters, start_from/due_by/assignee fields | "late / on time" filter and the advanced-filters UI |
| #732 | Add task data to print presets | `TemplateAssignmentContext.TASK_TYPE` defined (`backend/api/models/print.py:136`) | expose task form fields and linked-entity presets (with selection when multiple links) in the print preset builder |
| #734 | Handle task context in UI and events | `sendEvent` task linking, task store, backend event linking, suspend control (commit `c91836b6`) | explicit pause/resume cycle separate from suspend; pause-prevents-updates/navigation guard |
| #741 | Check file management with HTTPS | media endpoint preserves `Content-Type` (`backend/api/endpoints/media.py:104-118`) | explicit `Content-Disposition`; runtime DHR-download verification under HTTPS (no more `blob: http://...` insecure warnings) |
| #785 | Make task code and title non editable | task code is read-only in `TaskScreen.vue` | title still v-model bound when `editMode=true` (`TaskScreen.vue:199`) — should be locked post-creation like code |
| #788 | Ensure serial key uniqueness in counting | within-position dedup in `count_applied.py:96-140`; conflict detection in `count_session_confirmed.py:98-130` | cross-position uniqueness — same serial cannot be counted in multiple positions within the same session |

---

## Still open — not started (5)

| # | Title | Why open |
|---|---|---|
| #726 | Add "create task" action in serial, work order, issue and product | no create-task button in `ProductHome`, `WorkSessionScreen`, `IssueOverview`, `SerialDetail` |
| #739 | Limit BoM quantity to integer if component has traceability | `bom.py` `qt` is `float`; no conditional validation against `traceability_level` |
| #740 | Handle component quantity > 1 in SerialTree / serial-hierarchy | frontend `SerialTree` does not render multiplicity for components with qty > 1 |
| #787 | Handle task locking | no lock model on Task, no `TASK_LOCKED`/`UNLOCKED` events, no two-stage activation guard |
| #792 | Handle position-complete flag in case of movements | movement events don't check or clear `inventory_count_position_complete` when inventory changes |

---

## Out of scope for this triage

- **Milestone description checkboxes** (HTTPS / Print v2 deploy / Prefect 2→3 worker copy steps) — ops/deploy tasks, not coding issues.
- **Filing sub-issues** for the residual gaps in PARTIAL items — leave the gaps in the existing issue body unless the team prefers separate tickets.
- **Source code changes** — none performed; this triage is purely GitLab issue state reconciliation.
