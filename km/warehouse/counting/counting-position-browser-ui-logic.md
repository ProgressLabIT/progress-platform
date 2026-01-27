# Counting Browser - UI Logic Guide

This document describes the user interface logic for the counting components in the warehouse app, which are the main interfaces for inventory counting operations. It serves as a guide for understanding user flows and defining test cases.

---

## Overview

The warehouse app supports two types of counting sessions, each with its own primary component:

1. **Position-based counting** (`CountingPositionBrowser.vue`) - User selects a warehouse position first, then counts items within it
2. **Product-based counting** (`CountingProductBrowser.vue`) - User selects a product first, then counts that product's inventory across all positions

Both components share common building blocks:

- `CountingContentsView.vue` - Renders inventory items and handles counting operations
- `CountingProductList.vue` - Displays product search results with traceability-aware styling
- `CountingQuantityCard.vue` - Counting interface for non-serialized products
- `CountingSerialsCard.vue` - Counting interface for serialized products

### Shared Components

**`CountingContentsView.vue`** is responsible for:
- Rendering the inventory items list (products, serials, nested positions)
- Computing and displaying count status (started, completed, locked)
- Applying text and "hide counted" filters
- Aggregating serials by product
- Projecting **count-only** items (counts without inventory)
- Opening counting cards (`CountingQuantityCard`, `CountingSerialsCard`) for the selected item

**`CountingProductList.vue`** is responsible for:
- Rendering product items with traceability-aware icons (serialized vs non-serialized)
- Color-coded backgrounds (green for serialized, blue for non-serialized)
- Used by both `CountingProductBrowser.vue` and `CountingProductSearchCard.vue`

### State Management
The components use **Pinia** (`useCountingStore`) for managing:
- `sessionData` - The current counting session data
- `selectedPosition` - Currently selected position (for position-based counting)
- Navigation state across the counting workflow

---

# Part 1: Position-Based Counting

## Overview

`CountingPositionBrowser.vue` operates in two main views (determined by Pinia store state):
1. **Position Selection** - User selects a warehouse position to count (`countingStore.selectedPosition === null`)
2. **Contents View** - User views and counts items within the selected position (`countingStore.selectedPosition !== null`)

`CountingPositionBrowser.vue` focuses on:
- Position search and selection
- Position path / breadcrumb display
- Navigation (back / reset)
- Loading position contents, count records and position completion status from the API
- Delegating item interactions to `CountingContentsView.vue`

---

## Stage 1: Position Selection

### Initial State
- Search field is empty
- **Recent positions** are displayed (last 10 positions used in transfer movements)
- Label shows "POSIZIONI RECENTI"

### User Actions

#### 1.1 Search for a Position
| Action | Expected Behavior |
|--------|-------------------|
| User types in search field | System searches for positions matching the input |
| Search returns results | Display matching positions, label changes to "POSIZIONI DISPONIBILI" |
| Search returns no results | Display "No results" message |
| **Exact match found** (single result with code = search input) | **Auto-select** the position and proceed to Contents view |
| User clears search field | Reload and display recent positions |

#### 1.2 Select a Position
| Action | Expected Behavior |
|--------|-------------------|
| User clicks on a position card | Position is selected via `countingStore.setSelectedPosition()`, contents load |
| User clicks "Select Root Position" button | Position "IN" is selected as root |

#### 1.3 Duplicate Search Prevention
| Condition | Behavior |
|-----------|----------|
| Search value equals last search value | Search is skipped (no API call) |

---

## Stage 2: Contents View

### Initial State
- Selected position code is displayed in a chip
- Position contents are loaded from API (new structure: `{ position, path, contents }`)
- Position path is tracked for hierarchical navigation
- Count records for this position and session are loaded
- Search/filter field is available
- "Hide counted" checkbox is available

### Content Types

Items in a position can be of three types, each with distinct visual representation:

| Type | Icon | Background Color | Description |
|------|------|------------------|-------------|
| **Product** | `mdi-apps` | Blue backdrop | Non-serialized inventory |
| **Serial** | `mdi-cube-scan` | Green backdrop | Serialized/traced inventory |
| **Position** | `mdi-package-variant-closed` | Red backdrop | Nested position (clickable to drill down) |

### Special Item Types

#### Count-Only Items
Items that have count records but no physical inventory in the position.

| Visual Indicator | Behavior |
|------------------|----------|
| Grey backdrop (outline style) | Rendered without colored background |
| "ADDED" badge (orange) | Shows item was added during counting |

#### Aggregated Serials
Multiple serial items of the same product are **aggregated** into a single row.

| Behavior |
|----------|
| Shows product code (not individual serial codes) |
| Quantity reflects count of serials |
| Clicking opens serial counting card with all serials |

---

## Filtering Options

### Text Filter
- Filters are delegated to the backend via API call
- Filter applies to contents when search input changes

### Hide Counted Filter
| Checkbox State | Behavior |
|----------------|----------|
| Unchecked (default) | All items shown |
| Checked | Items with `completedCount > 0` are hidden from the list |

This allows users to focus only on items that still need to be counted.

---

## Item States and Indicators

### Count Progress Indicators

| State | Visual Indicator | Condition |
|-------|------------------|-----------|
| **Not started** | No special indicator | No count records exist |
| **Started by current user** | Blue border + "RIPRENDI" badge | Started record by current user |
| **Started by another user** | Orange "ATTIVO" badge | Started record by different user |
| **Completed** | Green checkmark icon | Completed/submitted/confirmed records |
| **Multiple completions** | "Nx" prefix before checkmark | More than one completed count |

### User Attribution

| Indicator | Condition |
|-----------|-----------|
| User avatar | Single user has worked on the item |
| Group icon (`mdi-account-group`) | Multiple users have completed counts |

### Performance Optimization
Count info is pre-computed using a `countInfoMap` computed property to avoid repeated filtering of records for each item. This map is rebuilt when:
- Position changes
- Count records change
- Filter changes

---

## Locking Mechanism

### Lock Rules

| Scenario | Behavior |
|----------|----------|
| Item has "started" record by **another user** | Access **blocked**, orange notification shown |
| Item has "started" record by **current user** | Access allowed, user can resume counting |
| Item has no started records | Access allowed |

### Aggregated Serial Locking
For aggregated serial items, locking is determined by checking all individual serials:

| Condition | Result |
|-----------|--------|
| All serials locked by same user | Aggregated item shown as locked by that user |
| Serials locked by different users | Item NOT shown as locked |
| Not all serials locked | Item NOT shown as locked |

---

## Navigation

### Hierarchical Position Navigation
The component tracks a **position path** for drill-down navigation through nested positions.

### Navigation Buttons

| Button | Visibility | Action |
|--------|------------|--------|
| **Back** | Only when `positionPath.length > 1` | Navigate to parent position (`goUpOneLevel()`) |
| **Reset** | Always in contents view | Return to position selection (`resetPositionNavigation()`) |

### Navigation Flow

```
Position Selection
       │
       ▼ selectPosition(pos)
  Position A (root)
       │
       ▼ click nested position
  Position B (child)
       │
       ├── "Back" button → Position A
       └── "Reset" button → Position Selection
```

### Path Handling
- Path is returned from API in response: `{ position, path, contents }`
- `goUpOneLevel()` uses `positionPath[positionPath.length - 2]` to find parent
- `resetPositionNavigation()` clears position in store and resets local state

---

## User Actions in Contents View

### 2.1 Filter Contents
| Action | Expected Behavior |
|--------|-------------------|
| User types in search field | API is called with search param, contents reloaded |
| Toggle "Hide counted" checkbox | Counted items are hidden/shown |
| Filter clears | All contents shown (based on checkbox state) |

### 2.2 Select an Item for Counting
| Item Type | Card Opened |
|-----------|-------------|
| Product (non-serial) | `CountingQuantityCard` |
| Serial/Aggregated Serial | `CountingSerialsCard` |
| Position | Navigate into that position (drill down) |

### 2.3 Add Count for Product
| Action | Expected Behavior |
|--------|-------------------|
| Click "Add count for product" button | Product search card opens |
| Search for product | Products matching search displayed |
| Select product | Counting card opens for that product in current position |

### 2.4 Navigate Back/Reset
| Action | Expected Behavior |
|--------|-------------------|
| Click "Back" button | Navigate to parent position (if path > 1) |
| Click "Reset" button | Return to position selection view |
| Store and local state cleared appropriately | |

---

## Product Search Card (Position-Based)

### Initial State
- Recent products displayed (last 10 used in movements)
- Label shows "Recenti"

### Product Search Flow

| Action | Expected Behavior |
|--------|-------------------|
| User types search | Products matching search displayed |
| Label changes to "Risultati" | |
| **Exact match found** | **Auto-select** product and open counting card |
| User clears search | Recent products displayed again |

### Product Visual Indicators

| Product Type | Icon | Background |
|--------------|------|------------|
| With traceability level (serial) | `mdi-cube-scan` | Green backdrop |
| Without traceability (quantity) | `mdi-apps` | Blue backdrop |

---

## Blind Mode

When the counting session has `blind_mode` enabled:

| Element | Behavior |
|---------|----------|
| Item quantities | **Hidden** from display |
| All other information | Displayed normally |

---

## API Response Structures

### Position Contents (GET `/position/{key}`)
New response structure:
```json
{
  "position": { "_key": "...", "code": "..." },
  "path": [
    { "_key": "root", "code": "ROOT" },
    { "_key": "child", "code": "CHILD" }
  ],
  "contents": [ /* inventory items */ ]
}
```

Fallback: Old format returns array of contents directly.

---

## Data Flow Summary (Position-Based)

```
┌─────────────────────────────────────────────────────────┐
│  Position Selection                                     │
│  (countingStore.selectedPosition === null)              │
└────────────────────────┬────────────────────────────────┘
                         │ selectPosition()
                         │ countingStore.setSelectedPosition()
                         ▼
┌─────────────────────────────────────────────────────────┐
│  Contents View                                          │
│  (countingStore.selectedPosition !== null)              │
│                                                         │
│  ┌─────────────────┐     ┌─────────────────┐           │
│  │  Position       │────▶│  Count Records  │           │
│  │  Contents       │     │  Loaded         │           │
│  └────────┬────────┘     └────────┬────────┘           │
│           │                       │                     │
│           └───────────┬───────────┘                     │
│                       ▼                                 │
│           ┌─────────────────────┐                       │
│           │  countInfoMap       │ (pre-computed)        │
│           │  (computed)         │                       │
│           └─────────────────────┘                       │
│                       │                                 │
│  ┌────────────────────┼────────────────────┐           │
│  │                    │                    │           │
│  ▼                    ▼                    ▼           │
│ selectItem()    Drill into pos    selectProductForCount│
│     │                 │                    │           │
│     ▼                 ▼                    ▼           │
│ Counting Cards    selectPosition()    Counting Cards   │
└─────────────────────────────────────────────────────────┘
         │                              │
         │ goUpOneLevel()               │ resetPositionNavigation()
         ▼                              ▼
    Parent Position              Position Selection
```

---

# Part 2: Product-Based Counting

## Overview

`CountingProductBrowser.vue` operates in two main views (determined by local component state):
1. **Product Selection** - User selects a product to count (`selectedProduct === null`)
2. **Contents View** - User views and counts inventory for the selected product (`selectedProduct !== null`)

Unlike position-based counting, product-based counting shows all inventory across all positions for a given product.

---

## Stage 1: Product Selection

### Initial State
- Search field is empty
- **Recent products** are displayed (last 10 products used in movements)
- Label shows "Recenti"

### User Actions

#### 1.1 Search for a Product
| Action | Expected Behavior |
|--------|-------------------|
| User types in search field | System searches for products matching the input |
| Search returns results | Display matching products, label changes to "Risultati" |
| Search returns no results | Display empty list |
| **Exact match found** (single result with code = search input) | **Auto-select** the product and proceed to Contents view |
| User clears search field | Reload and display recent products |

#### 1.2 Select a Product
| Action | Expected Behavior |
|--------|-------------------|
| User clicks on a product card | Product is selected, inventory for that product is loaded |

#### 1.3 Duplicate Search Prevention
| Condition | Behavior |
|-----------|----------|
| Search value equals last search value | Search is skipped (no API call) |

### Product Visual Indicators

| Product Type | Icon | Background |
|--------------|------|------------|
| With traceability level (serial) | `mdi-cube-scan` | Green backdrop |
| Without traceability (quantity) | `mdi-apps` | Blue backdrop |

---

## Stage 2: Contents View

### Initial State
- Selected product code is displayed in a chip with back button
- Product inventory (across all positions) is loaded from API
- Count records for this session and product are loaded
- Contents view uses `CountingContentsView.vue` for display and counting

### Content Types

For product-based counting, items can be:

| Type | Icon | Background Color | Description |
|------|------|------------------|-------------|
| **Product** | `mdi-apps` | Blue backdrop | Non-serialized inventory at a specific position |
| **Serial** | `mdi-cube-scan` | Green backdrop | Individual serial at a specific position |

Note: Position items are not shown in product-based counting (no drill-down navigation).

### Navigation

| Action | Expected Behavior |
|--------|-------------------|
| Click back arrow button | Return to product selection view |

---

## Data Flow Summary (Product-Based)

```
┌─────────────────────────────────────────────────────────┐
│  Product Selection                                      │
│  (selectedProduct === null)                             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Product Search (SearchOrScan)                   │   │
│  └──────────────────┬──────────────────────────────┘   │
│                     │                                   │
│  ┌──────────────────▼──────────────────────────────┐   │
│  │  CountingProductList                             │   │
│  │  (displays products with traceability styling)   │   │
│  └──────────────────┬──────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │ selectProduct()
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Contents View                                          │
│  (selectedProduct !== null)                             │
│                                                         │
│  ┌───────────────────────────────────────────┐         │
│  │  [Back] [Product Code Chip]               │         │
│  └───────────────────────────────────────────┘         │
│                                                         │
│  ┌─────────────────┐     ┌─────────────────┐           │
│  │  Product        │────▶│  Count Records  │           │
│  │  Inventory      │     │  Loaded         │           │
│  └────────┬────────┘     └────────┬────────┘           │
│           │                       │                     │
│           └───────────┬───────────┘                     │
│                       ▼                                 │
│           ┌─────────────────────┐                       │
│           │  CountingContentsView│                      │
│           └─────────────────────┘                       │
│                       │                                 │
│                       ▼                                 │
│               Counting Cards                            │
└─────────────────────────────────────────────────────────┘
         │
         │ resetProductSelection()
         ▼
    Product Selection
```

---

## Test Case Checklist

### Position Selection (Position-Based)
- [ ] Recent positions load on mount
- [ ] Search returns matching positions
- [ ] Exact match auto-selects position
- [ ] Empty search restores recent positions
- [ ] Duplicate search is prevented
- [ ] Root position "IN" can be selected
- [ ] Position is set in Pinia store on selection

### Product Selection (Product-Based)
- [ ] Recent products load on mount
- [ ] Search returns matching products
- [ ] Exact match auto-selects product
- [ ] Empty search restores recent products
- [ ] Duplicate search is prevented
- [ ] Product traceability icon displays correctly

### Contents View
- [ ] Contents load for selected position/product
- [ ] Position path is tracked from API response (position-based only)
- [ ] Count records load for session and position/product
- [ ] Count info map is pre-computed correctly
- [ ] Serial items are aggregated by product
- [ ] Count-only items appear for products with counts but no inventory
- [ ] Items sorted alphabetically by code

### Filtering
- [ ] Text filter triggers API call with search param
- [ ] "Hide counted" checkbox hides completed items
- [ ] "Hide counted" checkbox shows all items when unchecked
- [ ] Both filters work together correctly

### Item States
- [ ] Completed counts show checkmark
- [ ] Multiple completions show count prefix
- [ ] Started by current user shows "RIPRENDI" badge with blue border
- [ ] Started by another user shows "ATTIVO" badge
- [ ] User avatars/group icon display correctly

### Locking
- [ ] Items locked by other users are not accessible
- [ ] Notification shown when blocked
- [ ] Items locked by current user are accessible
- [ ] Aggregated serial locking logic works correctly

### Navigation (Position-Based)
- [ ] "Back" button only visible when positionPath.length > 1
- [ ] "Back" navigates to parent position
- [ ] "Reset" button always visible in contents view
- [ ] "Reset" returns to position selection
- [ ] Drilling into nested position updates path
- [ ] Path correctly reflects hierarchy

### Navigation (Product-Based)
- [ ] Back button returns to product selection
- [ ] Product chip displays selected product code

### Counting Cards
- [ ] Product items open CountingQuantityCard
- [ ] Serial items open CountingSerialsCard
- [ ] Nested positions navigate to that position (position-based only)
- [ ] Adding product for count opens correct card type

### Product Search
- [ ] Recent products load initially
- [ ] Search returns matching products
- [ ] Exact match auto-selects product
- [ ] Product type (serial/quantity) correctly identified
- [ ] Card closes and counting card opens on selection

### Blind Mode
- [ ] Quantities hidden when blind_mode is true
- [ ] Other item information still visible

### State Management
- [ ] Pinia store `selectedPosition` updates correctly (position-based)
- [ ] Local `selectedProduct` state updates correctly (product-based)
- [ ] `resetPositionNavigation()` clears store and local state
- [ ] Component reacts to store changes

---

## Edge Cases

| Scenario | Expected Behavior |
|----------|-------------------|
| Position has no contents | "No contents" message displayed |
| Product has no inventory | "No contents" message displayed |
| Position/Product search returns empty | "No results" message displayed |
| Count record for product not in inventory | Appears as count-only item |
| Multiple count records for same product | Only one row shown (aggregated) |
| Session user matches started record user | User can resume count |
| API returns old format (array) | Fallback handling, path is empty |
| All items are counted + "Hide counted" checked | Empty list shown |
| At root position, click "Back" | Falls back to position selection |
