---
created: 2026-03-20T23:06:16.419Z
title: Fix warehouse config store missing template fields in updateAppConfig
area: ui
files:
  - webapps/warehouse/src/stores/config.js:105-114
---

## Problem

`updateAppConfig()` in the warehouse config store does not include `product_label_template` or `position_label_template` in its PATCH body. The warehouse store reads these fields correctly (lines 70-71) but cannot write them back.

Currently not a functional bug because `WarehouseSettings.vue` is a main-app component that routes through the main app's config store (which does include both fields). But if any warehouse-app code ever calls the warehouse store's `updateAppConfig` for these fields, the values will be silently dropped.

## Solution

Add `product_label_template` and `position_label_template` to the PATCH body in `webapps/warehouse/src/stores/config.js` `updateAppConfig()`, matching the pattern in `webapps/main/src/stores/config.js` lines 163-164.
