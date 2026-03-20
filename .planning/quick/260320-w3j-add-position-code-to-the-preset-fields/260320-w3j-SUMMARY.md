---
phase: quick
plan: 260320-w3j
subsystem: print
tags: [preset-fields, template-context, position]
dependency_graph:
  requires: []
  provides: [position.code preset in designer dropdown, TemplateContext.setSelectedPosition()]
  affects: [webapps/main/src/lib/print/index.js, webapps/main/src/lib/print/plugins/linkConfig.js]
tech_stack:
  added: []
  patterns: [TemplateContext setter pattern, preset switch case pattern]
key_files:
  created: []
  modified:
    - webapps/main/src/lib/print/plugins/linkConfig.js
    - webapps/main/src/lib/print/index.js
decisions:
  - position added as a first-class TemplateContext property following the serial/product/workOrder/issue pattern
metrics:
  duration: 5 min
  completed_date: "2026-03-20T22:10:55Z"
---

# Quick Task 260320-w3j: Add position.code to the Preset Fields Summary

**One-liner:** Added `position.code` preset to the designer dropdown and wired it to `TemplateContext.position?.code` at runtime via a new `setSelectedPosition()` method.

## What Was Done

- `linkConfig.js`: Added `'position.code'` to `presetOptions` array, placed between `product.description` and `issue.id`
- `index.js`: Added `position = null` class property to `TemplateContext`
- `index.js`: Added `this.position = null` to `resetState()`
- `index.js`: Added `case 'position.code': return this.position?.code;` in `getPresetValue()` switch (new "Position presets" block after product presets)
- `index.js`: Added `setSelectedPosition(position)` method following the existing setter pattern
- `index.js`: Added `position: this.position` to `baseObjectMap` in `getExtraValue()` so `position.extra.*` paths work

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add position.code to preset options and TemplateContext | b756a12f | linkConfig.js, index.js |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- `webapps/main/src/lib/print/plugins/linkConfig.js` — FOUND: `'position.code'`
- `webapps/main/src/lib/print/index.js` — FOUND: `case 'position.code':`
- `webapps/main/src/lib/print/index.js` — FOUND: `position: this.position,`
- Commit b756a12f — FOUND in git log
