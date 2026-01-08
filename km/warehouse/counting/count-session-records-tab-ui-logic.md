# Count Session Records Tab - UI Logic Guide

This document describes the user interface logic for the **CountSessionRecordsTab** component, which displays aggregated count records for a session with filtering, conflict resolution, and export/import capabilities.

---

## Overview

The `CountSessionRecordsTab.vue` component provides a tabular view of count records aggregated by product and position. It supports:
- **Level-based position aggregation** (view records at different hierarchy depths)
- **Multi-dimensional filtering** (variance, product, position, serial, user, notes)
- **Conflict detection and resolution** (when multiple users count the same item differently)
- **Export/Import functionality** (XLSX, CSV)

### State Management
The component uses:
- **Pinia** (`useCountSessionStore`) for session data and raw records
- **Local refs** for UI state (filters, display mode, selected level)
- **Vuex** for user data lookup (`store.getters.getUserByKey`)

---

## UI Organization

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  q-splitter (70/30 split)                                       │
│  ┌─────────────────────────────────────┐┌─────────────────────┐ │
│  │  MAIN CONTENT (before)              ││  FILTER SIDEBAR     │ │
│  │  ┌────────────────────────────────┐ ││  (after)            │ │
│  │  │  q-table (virtual-scroll)      │ ││  ┌────────────────┐ │ │
│  │  │  - Product column              │ ││  │ Export/Import  │ │ │
│  │  │  - Position column             │ ││  │ buttons        │ │ │
│  │  │  - User column                 │ ││  ├────────────────┤ │ │
│  │  │  - Counted At column           │ ││  │ Variance       │ │ │
│  │  │  - System Qt column            │ ││  │ filters        │ │ │
│  │  │  - Counted Qt column           │ ││  ├────────────────┤ │ │
│  │  │  - Delta column                │ ││  │ Position Level │ │ │
│  │  │  - Notes column                │ ││  │ selector       │ │ │
│  │  │  - Conflict column             │ ││  ├────────────────┤ │ │
│  │  └────────────────────────────────┘ ││  │ Text filters   │ │ │
│  │  ┌────────────────────────────────┐ ││  │ (product,      │ │ │
│  │  │  Footer: Row counts +          │ ││  │  serial,       │ │ │
│  │  │  discarded info                │ ││  │  position,     │ │ │
│  │  └────────────────────────────────┘ ││  │  user, tag)    │ │ │
│  └─────────────────────────────────────┘│  └────────────────┘ │ │
│                                          └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Empty State
When no visible records exist:
- Shows "No data" message
- If discarded records exist, shows count of hidden discarded records

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│  DATA SOURCE                                                          │
│  countSessionStore.records (raw records from API)                     │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  AGGREGATION LAYER                                                    │
│  aggregatedRecords (computed)                                         │
│  - Groups by product_key + aggregated_position_key                    │
│  - Applies level-based position aggregation                           │
│  - Calculates totals, deltas, serial diffs                            │
│  - Detects conflicts and tracks multi-user counts                     │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  VISIBILITY FILTER                                                    │
│  visibleAggregates (computed)                                         │
│  - Excludes aggregates with ONLY discarded records                    │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  USER FILTERS                                                         │
│  filteredRecords (computed)                                           │
│  - Variance threshold (absolute/percentage)                           │
│  - Only with variance                                                 │
│  - Has notes                                                          │
│  - Product text/tag                                                   │
│  - Serial                                                             │
│  - Position (with optional path matching)                             │
│  - User                                                               │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│  DISPLAY                                                              │
│  q-table renders filteredRecords                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Aggregation Logic

### Level-Based Position Aggregation

The component supports viewing records at different position hierarchy levels. This allows users to see totals at warehouse zones, aisles, or individual bins.

#### Level Concept

| User Level | Description | Position Path Example |
|------------|-------------|----------------------|
| 0 | Root (IN) - Total inventory | `IN` |
| 1 | First-level children of IN | `Zone-A` |
| 2 | Second-level (grandchildren) | `Zone-A > Aisle-1` |
| 3+ | Deeper levels | `Zone-A > Aisle-1 > Bin-01` |
| All | Most granular (actual position) | Full path to leaf position |

#### `getAggregatePosition()` Function

This function determines which position to use for aggregation based on the selected level:

| Condition | Behavior |
|-----------|----------|
| `allLevels === true` | Use actual position (no aggregation) |
| `selectedLevel === 0` | Aggregate at root (all positions → "IN") |
| `selectedLevel >= 1` | Use ancestor at that level, or actual if shallower |

#### Example

Given a record at position `Zone-A > Aisle-1 > Bin-01` (level 3):

| Selected Level | Aggregate Position | Result |
|----------------|-------------------|--------|
| 0 | IN | Totals for entire warehouse |
| 1 | Zone-A | Totals for zone |
| 2 | Zone-A > Aisle-1 | Totals for aisle |
| 3 or "All" | Zone-A > Aisle-1 > Bin-01 | Actual position |

### Aggregate Object Structure

Each aggregate object contains:

```javascript
{
  aggregateKey: 'product_key_position_key',
  product: { key, code, description, traceability_level, tags },
  position: { key, code, deleted },
  pathString: 'Zone-A > Aisle-1',
  records: [ /* original records */ ],
  
  // Calculated quantities (null if records don't match)
  totalSystemQt: Number | null,
  totalCountedQt: Number | null,
  delta: Number | null,
  
  // Serial tracking
  allSystemSerialCodes: Set,
  allCountedSerialCodes: Set,
  serialDelta: { added: [], removed: [] },
  
  // Conflict and notes
  hasConflict: Boolean,
  hasNotes: Boolean,
  notesCount: Number,
  allNotes: [],
  
  // User tracking
  userKeys: [],
  hasMultipleUsers: Boolean,
  user_key: String | null,
  counted_at: Date | null,
  
  // Position aggregation tracking
  aggregatedPositionKeys: [],
  aggregatedPositionCodes: [],
  
  // Coverage tracking
  coverage: {
    positionKey: String,    // The aggregated position key being checked
    isComplete: Boolean,    // true if position is in completedPositions
    isAggregated: Boolean,  // true when aggregating (not in "All levels" mode)
  },
  
  // For compatibility
  activeRecordKey: String | null,
  
  // Uncounted inventory tracking (Phase 3)
  // Note: These are computed dynamically from cache, not stored on aggregate
  // Use helper functions: getUncountedQt(), getTotalSystemQt(), getEffectiveDelta()
}
```

### Quantity Matching Logic

When aggregating multiple records:

| Scenario | totalSystemQt | totalCountedQt |
|----------|---------------|----------------|
| All records have same system_qt | That value | - |
| Records have different system_qt | `null` | - |
| All records have same counted_qt | - | That value |
| Records have different counted_qt | - | `null` |

When quantities are `null`, the UI shows `?` or conflict indicators.

### Conflict Detection

Conflicts are detected at the **original product/position pair level** (not at the aggregated level):

1. Group records by `product_key + position_key`
2. For each pair, check if multiple non-discarded records have different `counted_qt`
3. If any pair has conflicts, set `hasConflict = true` on the aggregate

### Coverage Tracking

When aggregating records at a specific level (not "All levels"), the displayed data may not include all inventory in that position because not all sub-positions have been counted.

#### Data Source

Coverage is determined using the `inventory_count_position_complete` edge collection, which tracks positions that have been fully counted for a session. This collection is populated by:
- `CountCompletedEvent`: When a count is completed, it checks if all items in the position have been counted
- `PositionConfirmedEmptyEvent`: When a position is confirmed as empty

#### Coverage Logic

1. On component mount, `loadCompletedPositions()` fetches all completed position keys for the session via `GET /inventory/count-session/{key}/completed-positions`
2. Results are stored as a `Set` in `countSessionStore.completedPositions` for O(1) lookups
3. Each aggregate object includes a `coverage` property with:
   - `positionKey`: The aggregated position key being checked
   - `isComplete`: `true` if the position is in `completedPositions`
   - `isAggregated`: `true` when aggregating (not in "All levels" mode)

#### UI Display

| State | Icon | Color | Tooltip |
|-------|------|-------|---------|
| Position fully counted | `mdi-check-circle` | `positive` (green) | "Position fully counted" |
| Position NOT fully counted | `mdi-alert-circle-outline` | `warning` (orange) | "Position not fully counted - data may be incomplete" |
| "All levels" mode | No icon | - | Coverage is implicit (each row is granular) |

---

## Uncounted Inventory Tracking (Phase 3)

When aggregating records at a specific level (not "All levels" mode), the displayed data may not represent the complete inventory picture because some positions may not have been counted. Phase 3 adds visibility into inventory that exists in positions that weren't counted.

### Data Flow

1. For each aggregate where `coverage.isAggregated && !coverage.isComplete`:
   - Fetch current inventory via `/inventory?root_position_key={positionKey}&product_key={productKey}`
   - Filter results to exclude positions in `aggregatedPositionKeys` (already counted)
   - Sum remaining quantities = `uncountedQt`
   - Calculate `totalSystemQt = systemQt + uncountedQt`

2. Fetching is sequential (one aggregate at a time) to avoid overwhelming the backend

3. Results are cached in `countSessionStore.uncountedInventoryCache` by `positionKey_productKey` and persist across level changes

4. Cache is cleared when records change (via SSE inventory notifications)

### Store State

```javascript
// countSessionStore
uncountedInventoryCache: new Map(), // key: "positionKey_productKey" -> { qt, positions, loading, error }
// positions: Array<{ key, code, quantity }> - sorted by quantity descending
```

### Helper Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `getUncountedData(row)` | `{ qt, positions, loading, error }` | Get cached data for a row |
| `getUncountedQt(row)` | `number \| null` | Get uncounted quantity (0 if complete) |
| `getUncountedPositions(row)` | `Array<{ key, code, quantity }>` | Get uncounted positions for tooltip |
| `getTotalSystemQt(row)` | `number \| null` | System Qt + Uncounted Qt |
| `getEffectiveDelta(row)` | `number \| null` | Delta using total system when aggregating |
| `isUncountedLoading(row)` | `boolean` | Check if data is loading |
| `getUncountedError(row)` | `string \| null` | Get error message if fetch failed |
| `retryUncountedFetch(row)` | `Promise<void>` | Retry failed fetch |

### Column Display (Aggregating Mode Only)

| Column | Source | When Shown |
|--------|--------|------------|
| System Qt | Sum of `system_qt` from count records | Always |
| Uncounted Qt | Fetched inventory in uncounted positions | Only when aggregating (not "All levels") |
| Total System Qt | System Qt + Uncounted Qt | Only when aggregating (not "All levels") |

### Delta Calculation

| Mode | Delta Calculation |
|------|-------------------|
| "All levels" | `counted_qt - system_qt` (from records) |
| Aggregating, complete coverage | `counted_qt - system_qt` (uncounted = 0) |
| Aggregating, incomplete coverage | `counted_qt - totalSystemQt` |

### Loading States

| State | Uncounted Qt | Total System Qt | Delta |
|-------|--------------|-----------------|-------|
| Loading | `q-spinner-tail` | `q-spinner-tail` | `q-spinner-tail` |
| Error | Error icon (clickable to retry) | `?` | `?` |
| Complete | Numeric value (warning color if > 0) + tooltip with positions | Numeric value | Colored numeric value |

### Uncounted Qt Tooltip

When hovering over a non-zero uncounted quantity, a tooltip displays:
- Header: "Uncounted Positions"
- List of positions with their quantities (up to 10, sorted by quantity descending)
- "+N more" indicator if more than 10 positions exist

---

## Filtering System

### Filter State

```javascript
filters: {
  variance: Number | null,      // Threshold value
  varianceType: 'absolute' | 'percentage',
  onlyWithVariance: Boolean,    // Only show records with delta != 0
  onlyConflicts: Boolean,       // Only show records with conflicts
  hasNotes: Boolean,            // Only show records with notes
  product: String,              // Product code/description filter
  serial: String,               // Serial code filter
  position: String,             // Position code filter
  positionIncludePath: Boolean, // Also match ancestors/children
  productTag: String | null,    // Product tag key
  userKey: String | null,       // User key
}
```

### Filter Logic

| Filter | Matching Logic |
|--------|----------------|
| **Variance threshold** | `abs(delta) >= threshold` (absolute) or `(abs(delta) / system_qt) * 100 >= threshold` (percentage) |
| **Only with variance** | `abs(delta) > 0` |
| **Only conflicts** | `aggregate.hasConflict === true` |
| **Has notes** | `aggregate.hasNotes === true` |
| **Product** | Wildcard match on `product.code` OR `product.description` |
| **Serial** | Wildcard match on any serial in any record of aggregate |
| **Position** | Wildcard match on `position.code` |
| **Position (include path)** | Also matches path string, path codes, aggregated position codes, and underlying record paths |
| **Product tag** | `product.tags` contains selected tag key |
| **User** | `aggregate.userKeys` includes selected user key |

### Wildcard Matching

Uses the `useWildcardToRegex` composable for pattern matching:
- `*` matches any characters
- `?` matches single character
- Case-insensitive by default

---

## Table Columns

| Column | Display | Special Handling |
|--------|---------|------------------|
| **Product** | Code + description (truncated) | Tooltip shows full values |
| **Position** | Code with badge for aggregated count | Strikethrough if deleted; tooltip shows path and aggregated positions |
| **User** | Avatar or group icon | Group icon when multiple users |
| **Counted At** | Formatted datetime | Hidden when conflict or multiple users |
| **System Qt** | Total or `-` | Shows `-` if records don't match |
| **Uncounted Qt** | Number or spinner | Hidden in "All levels" mode; 0 if coverage.isComplete; warning color if > 0 |
| **Total System Qt** | Number or spinner | Hidden in "All levels" mode; equals System Qt if coverage.isComplete |
| **Counted Qt** | Total or conflict button | Alert button opens conflict dialog |
| **Delta** | Colored value or serial diff | Green for +, red for -, uses total system when aggregating |
| **Notes** | Icon with badge | Badge shows count, tooltip lists all notes |
| **Conflict** | Info button | Shows discarded records count |

### Delta Display Logic

| Condition | Display |
|-----------|---------|
| System or counted is null | `?` (grey) |
| No active record | `-` (grey) |
| Has serial delta (added or removed) | `+N` (green) / `-N` (red) for serials |
| Numeric delta > 0 | `+N` (green, bold) |
| Numeric delta < 0 | `N` (red, bold) |
| Numeric delta = 0 | `0` (grey) |

---

## Conflict Resolution

### Conflict Dialog Flow

1. User clicks conflict button on row with `hasConflict = true` OR discarded records
2. `CountRecordConflictDialog` opens with aggregate data
3. Dialog groups records by original product/position pair
4. For each pair with conflicts:
   - Shows all non-discarded records with radio selection
   - User selects which record to keep
   - Other records are discarded via `countSessionStore.discardRecords()`
5. Navigation between multiple conflicting pairs within same aggregate
6. On resolution, parent reloads records

### Dialog Features

| Feature | Description |
|---------|-------------|
| Multi-pair navigation | Arrow buttons to move between conflicting pairs |
| Pre-selection | Most recent record is pre-selected |
| Discarded records | Shown in collapsible section for reference |
| Read-only mode | If no actual conflict (just discarded records), no selection UI |

---

## Export/Import

### Export (`useCountRecordExport` composable)

| Format | Description |
|--------|-------------|
| XLSX | Excel format with translated column headers |
| CSV | Comma-separated with translated headers |

#### Export Behavior

- Fetches **all session records** (bypasses UI filters)
- Explodes serialized records to individual rows
- Removed serials exported with `counted_qt = 0`
- Filename: `count_session_{code}_{date}`

#### Export Columns

| Column | Description |
|--------|-------------|
| Position | Position code |
| Product | Product code |
| Serial | Serial code (empty for non-serialized) |
| System Qt | Expected quantity |
| Counted Qt | Counted quantity |
| Delta | Difference |
| Username | Full name of user who counted |
| Counted At | Timestamp |

### Import

Opens `CountRecordImportDialog` for uploading count data from external sources.

---

## Real-Time Updates

The component subscribes to Server-Sent Events for automatic updates:

```javascript
// On mount
events.value = new EventSource(`${api.defaults.baseURL}/notification/inventory-notification`);
events.value.addEventListener('inventory-notification', () => {
  loadRecords();
});
```

This ensures the table reflects the latest count data when other users submit counts.

---

## Performance Considerations

### Virtual Scrolling
Table uses `virtual-scroll` for efficient rendering of large datasets.

### Pre-computed Aggregation
Aggregation is performed once in `aggregatedRecords` computed property, not per-render.

### Wildcard Matchers
Matchers are built once at filter computation time via `buildWildcardMatcher()`.

---

## Test Case Checklist

### Data Loading
- [ ] Records load from store on mount
- [ ] Position hierarchy loads for level aggregation
- [ ] Loading indicator shows during fetch
- [ ] Empty state displays when no records

### Level Aggregation
- [ ] Level 0 aggregates all positions to "IN"
- [ ] Level 1 groups by first-level position
- [ ] "All" toggle shows most granular positions
- [ ] Level input updates aggregation correctly
- [ ] Aggregated position badge shows count
- [ ] Tooltip lists all aggregated position codes

### Quantity Calculations
- [ ] Matching system quantities show single value
- [ ] Non-matching system quantities show null
- [ ] Matching counted quantities show single value
- [ ] Non-matching counted quantities show null
- [ ] Delta calculated only when both quantities available

### Conflict Detection
- [ ] Conflicts detected at pair level within aggregate
- [ ] Conflict button appears for conflicting rows
- [ ] Conflict dialog opens with correct data
- [ ] Multi-pair navigation works
- [ ] Discard resolution updates records

### Coverage Indicator
- [ ] Completed positions loaded on mount via `loadCompletedPositions()`
- [ ] Coverage icon shown when aggregating (not in "All levels" mode)
- [ ] Green check icon for fully counted positions
- [ ] Orange warning icon for incomplete positions
- [ ] Coverage icon hidden in "All levels" mode
- [ ] Tooltip shows appropriate message for each state
- [ ] Completed positions refresh on inventory-notification event

### Uncounted Inventory (Phase 3)
- [ ] Uncounted Qt column hidden in "All levels" mode
- [ ] Total System Qt column hidden in "All levels" mode
- [ ] Uncounted Qt shows 0 when position is fully counted (coverage.isComplete)
- [ ] Uncounted Qt fetches correctly for incomplete positions
- [ ] Spinner shown while fetching uncounted inventory
- [ ] Cache prevents re-fetching on level changes
- [ ] Sequential fetching (not parallel) prevents backend overload
- [ ] Error state shows error icon with retry option
- [ ] Total System Qt = System Qt + Uncounted Qt
- [ ] Delta uses Total System Qt when aggregating with incomplete coverage
- [ ] Cache clears when records change via SSE notification

### Filtering
- [ ] Variance threshold filters correctly (absolute)
- [ ] Variance threshold filters correctly (percentage)
- [ ] "Only with variance" hides zero-delta rows
- [ ] "Only conflicts" filters to rows with hasConflict = true
- [ ] "Has notes" filters to rows with notes
- [ ] Product text filter matches code and description
- [ ] Serial filter matches across all records in aggregate
- [ ] Position filter matches code
- [ ] Position with path includes ancestors and children
- [ ] User filter matches userKeys array
- [ ] Product tag filter matches tag array

### User Display
- [ ] Single user shows avatar
- [ ] Multiple users show group icon
- [ ] User tooltip shows names
- [ ] Timestamp hidden when multiple users

### Serial Handling
- [ ] Serial delta shows added/removed counts
- [ ] Tooltip lists individual serial codes
- [ ] Serials union across all records in aggregate

### Export/Import
- [ ] XLSX export downloads file
- [ ] CSV export downloads file
- [ ] Export includes all session records (not filtered)
- [ ] Import dialog opens and processes file

### Real-Time Updates
- [ ] EventSource subscription established on mount
- [ ] Records reload on inventory-notification event
- [ ] EventSource closed on unmount

### Discarded Records
- [ ] Discarded-only aggregates hidden from main view
- [ ] Discarded count shown in footer
- [ ] Discarded records visible in conflict dialog

---

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| All records discarded for aggregate | Aggregate hidden, counted in footer |
| Position deleted after counting | Strikethrough on position code, tooltip warning |
| No position data | Position column shows `-` |
| Serial product with no serials | Falls back to quantity delta |
| Very deep position hierarchy | Level input accepts any value, capped at actual depth |
| Filter matches no records | Table shows empty with "No data" message |
| Export with zero records | Warning notification shown |
| Conflict in aggregated view but not at pair level | No conflict button (aggregation masks pair-level match) |
| Uncounted inventory fetch fails | Show error icon in Uncounted Qt, `?` in Total System and Delta, retry available |
| Product only exists in uncounted positions | System Qt = 0 from records, Uncounted Qt = fetched value, row won't appear (no count records) |
| Session has no incomplete positions | Uncounted columns show 0, no fetches needed |
| Inventory moved after counting | Uncounted Qt reflects current inventory, may show discrepancy |

