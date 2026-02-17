# Phase 3 Research: Frontend Display Cleanup

**Created:** 2026-02-17
**Phase:** 03-frontend-display-cleanup

## Research Objective

Understand how float values are currently displayed in Vue components and identify all locations that need clean numeric formatting to prevent floating-point noise in the UI.

## Current State Analysis

### 1. Existing Float Formatting

**Found partial solution:**
- `MovementsRoot.vue` line 458 has a local `roundQuantity()` function
- Rounds to 4 decimal places: `Math.round(value * 10 ** 4) / 10 ** 4`
- Only used in one component (warehouse movements)
- Not consistent with backend 6-decimal standard

**Global filters in `boot/filters.js`:**
- `$numberFormat(value, locale)` - Uses `Intl.NumberFormat` for locale formatting
- `$durationFromMillisec()` - For time durations (uses integer operations)
- No general-purpose float precision filter exists

### 2. Problem Locations Identified

**Production displays (raw float values):**
- `JobCard.vue` line 68: `{{ job.qt_completed }} / {{ job.qt_planned }}`
- `JobCard.vue` line 84: `{{ job.progress }}%`
- `JobCardSlim.vue` line 56: Similar pattern
- `ProgressBtn.vue`: Calculations with `qt_planned - qt_completed`
- `ProductionAdminMenu.vue`: Multiple quantity displays and calculations

**Warehouse displays:**
- `MovementsRoot.vue` line 116: Uses `roundQuantity()` (already partially fixed)
- Inventory quantity displays (need to verify specific files)
- Position displays (need to verify)

**Work sessions:**
- Duration formatting already uses integer-based functions (no float issue)
- Batch completion quantities may need formatting

### 3. Architecture Pattern

Vue 3 with:
- Composition API available
- Global filters registered in `boot/` directory
- Composables in `src/composables/`
- Components can use either Options API or Composition API

## Implementation Strategy

### Option 1: Global Filter (Recommended)
**Pros:**
- Simple template usage: `{{ value | formatFloat }}`
- Centralized logic
- Easy to apply across all components
- Consistent with existing filter pattern

**Cons:**
- Vue 3 deprecated template filters (but Quasar may still support them)
- Need to verify Quasar/Vue 3 filter support

### Option 2: Composable
**Pros:**
- Modern Vue 3 pattern
- Can be used in both template and script
- Supports Composition API

**Cons:**
- Requires import in each component
- More verbose in templates: `{{ formatFloat(value) }}`

### Option 3: Global Property (Recommended Fallback)
**Pros:**
- Works like filters: `{{ $formatFloat(value) }}`
- Consistent with existing `$numberFormat`, `$durationFromMillisec`
- No imports needed
- Works in both Options and Composition API

**Cons:**
- Not as clean as filters
- Slightly more verbose

**Decision:** Use **Option 3 (Global Property)** - matches existing pattern in `boot/filters.js`

## Formatting Requirements

### Core Function Specification

```javascript
/**
 * Format float value for display with clean precision.
 *
 * @param {number} value - Float value to format
 * @param {number} maxDecimals - Maximum decimal places (default: 6)
 * @param {boolean} stripTrailingZeros - Remove trailing zeros (default: true)
 * @returns {string|number} Formatted value
 */
function formatFloat(value, maxDecimals = 6, stripTrailingZeros = true) {
  if (value === null || value === undefined) return '-';
  if (typeof value !== 'number') return value;
  if (!isFinite(value)) return value; // Handle Infinity, -Infinity
  if (isNaN(value)) return '-';

  // Round to maxDecimals
  const rounded = Math.round(value * 10 ** maxDecimals) / 10 ** maxDecimals;

  if (stripTrailingZeros) {
    // Convert to string and remove trailing zeros
    return parseFloat(rounded.toFixed(maxDecimals));
  }

  return rounded;
}
```

### Usage Patterns

**In templates:**
```vue
<!-- Quantities -->
{{ $formatFloat(job.qt_completed) }} / {{ $formatFloat(job.qt_planned) }}

<!-- Progress -->
{{ $formatFloat(job.progress, 2) }}%

<!-- Inventory -->
{{ $formatFloat(inventory.available_quantity) }}
```

**Special cases:**
- Progress percentages: 2 decimals max (e.g., "99.99%")
- Quantities: 6 decimals max (default)
- Costs/values: 2 decimals (currency formatting)

## Files Requiring Changes

### Wave 1: Create Utility
1. `boot/filters.js` - Add `$formatFloat` global property

### Wave 2: Production Components
1. `components/JobCard.vue` - qt_completed, qt_planned, progress
2. `components/JobCardSlim.vue` - qt_completed, qt_planned
3. `components/ProgressBtn.vue` - quantity calculations
4. `components/ProductionAdminMenu.vue` - multiple quantity displays
5. `components/MediaViewer.vue` - quantity display
6. `components/OperatorJobsReorderDialog.vue` - qt_completed, qt_planned

### Wave 3: Warehouse Components
1. `views/warehouse/movements/MovementsRoot.vue` - replace local roundQuantity
2. Inventory quantity displays (to be identified during implementation)
3. Position displays (to be identified during implementation)

## Edge Cases to Handle

1. **Null/undefined values:** Display as "-"
2. **NaN values:** Display as "-"
3. **Infinity values:** Display as-is or handle specially
4. **Non-numeric values:** Return as-is
5. **Zero values:** Display as "0" (no trailing decimals)
6. **Very small values:** Display correctly (e.g., 0.000001)

## Success Criteria

1. ✅ Global `$formatFloat()` function available in all components
2. ✅ Quantities display without precision noise (e.g., "100" not "100.000001")
3. ✅ Progress percentages show max 2 decimals
4. ✅ Consistent formatting across production and warehouse views
5. ✅ Edge cases (null, NaN, Infinity) handled gracefully
6. ✅ No breaking changes to existing functionality

## Testing Approach

Manual verification:
1. View job cards with various quantity values
2. Check movement displays in warehouse
3. Verify progress percentages display correctly
4. Test edge cases (null, 0, very small numbers)
5. Confirm no visual regressions

---
*Research completed: 2026-02-17*
