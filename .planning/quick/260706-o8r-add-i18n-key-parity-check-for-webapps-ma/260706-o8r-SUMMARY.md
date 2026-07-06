---
phase: quick-260706-o8r
plan: "01"
subsystem: webapp-i18n
tags: [i18n, tooling, parity-check, webapp-main]
dependency_graph:
  requires: []
  provides: [i18n-parity-tooling]
  affects: [webapps/main/package.json]
tech_stack:
  added: []
  patterns: [dependency-free ESM script, dynamic import()]
key_files:
  created:
    - webapps/main/scripts/check-i18n-parity.js
  modified:
    - webapps/main/package.json
decisions:
  - "Parity check exits non-zero on current tree; lint left unchained to avoid breaking yarn lint"
  - "Drift recorded for follow-up, locale files not modified by this plan"
metrics:
  duration: ~5min
  completed: 2026-07-06
---

# Phase quick-260706-o8r Plan 01: Add i18n Key-Parity Check Summary

Dependency-free ESM script (`scripts/check-i18n-parity.js`) + `yarn i18n:check` npm script that recursively compares dotted key paths from `src/i18n/en.js` vs `src/i18n/it.js` and exits non-zero with a per-locale grouped missing-key report.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write dependency-free key-parity checker | ec9ad0bd | webapps/main/scripts/check-i18n-parity.js |
| 2 | Wire i18n:check script in package.json | ec9ad0bd | webapps/main/package.json |

## Verification Results

- `yarn i18n:check` runs and exits 1 (pre-existing drift detected — correct behavior).
- `yarn lint` script unchanged (`yarn lint:check --fix`) — not broken.
- Only `scripts/check-i18n-parity.js` and `package.json` staged and committed; locale/traceability files untouched.

## Deviations from Plan

None — plan executed exactly as written. Parity check failed on current tree as predicted by the planner; lint left unchained per the conditional branch in Task 2.

## Pre-existing i18n drift (follow-up)

The parity check fails on the current tree. Full output of `node scripts/check-i18n-parity.js`:

**Missing from it.js (16 keys):**
```
bom.view
dismiss
phase.label
serial_field.serial_link_process_inventory.new_link
serial_field.serial_link_process_inventory.old_link
serial_field.serial_not_available_confirmation
serial_field.serial_not_available_confirmation_message
serial_field.serial_used_confirmation
serial_field.serial_used_confirmation_message
warehouse.consumption_options.mandatory_quantity
warehouse.consumption_options.mandatory_quantity_if_negative
warehouse.counting.has_notes
warehouse.movement.revert_error
warehouse.movement.revert_success
work_order.list_headers.wo_line
write
```

**Missing from en.js (7 keys):**
```
active_qt
equipment_classes
issue_types_alerts_delete_general_error
loading_signal.default_title
massCopyProcess.copyToAllProducts
warehouse.counting.data
warehouse.counting.error
```

**Summary:** 16 keys missing from it.js, 7 keys missing from en.js, 1249 keys common to both.

To resolve: add the missing translations to the respective locale files and re-run `yarn i18n:check`. Once parity is clean, chain it into `lint` with `"lint": "yarn i18n:check && yarn lint:check --fix"`.

## Self-Check: PASSED

- `webapps/main/scripts/check-i18n-parity.js` exists and runs without throwing.
- `webapps/main/package.json` contains `i18n:check` script.
- Commit ec9ad0bd exists on DEV.
- Unrelated pending changes (traceability, locale files) are not staged/committed.
