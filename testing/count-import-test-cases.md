# Count Record Import - Test Cases

This document outlines test cases for the count record import functionality.

## Prerequisites

- A count session exists and is in "started" status
- Test products, positions, and serials exist in the database
- User has appropriate permissions

---

## 1. File Upload & Validation

### 1.1 File Format Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 1.1.1 | Valid CSV file | `.csv` file with correct columns | File accepted, validation proceeds |
| 1.1.2 | Valid XLSX file | `.xlsx` file with correct columns | File accepted, validation proceeds |
| 1.1.3 | Invalid file type | `.txt`, `.pdf`, or other file | Error: "Invalid file type" |
| 1.1.4 | Empty file | Empty CSV/XLSX | Error: "No data rows found" |
| 1.1.5 | File with BOM | CSV with UTF-8 BOM | File parsed correctly |

### 1.2 Column Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 1.2.1 | All required columns | `position_code`, `product_code`, `counted_qt` | Validation proceeds |
| 1.2.2 | Missing position_code | File without position_code column | Error: "Missing required columns: position_code" |
| 1.2.3 | Missing product_code | File without product_code column | Error: "Missing required columns: product_code" |
| 1.2.4 | Missing counted_qt | File without counted_qt column | Error: "Missing required columns: counted_qt" |
| 1.2.5 | Extra columns | File with additional columns (notes, etc.) | Extra columns ignored, validation proceeds |
| 1.2.6 | Column name variations | Headers with different casing (Position_Code) | Should be case-insensitive |

---

## 2. Data Validation

### 2.1 Product Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 2.1.1 | Valid product code | Existing product code | Row validated |
| 2.1.2 | Invalid product code | Non-existent product code | Error file with "Product 'XXX' not found" |
| 2.1.3 | Empty product code | Row with blank product_code | Error file with "Missing product_code" |
| 2.1.4 | Multiple invalid products | Several rows with bad product codes | Error file shows all errors |

### 2.2 Position Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 2.2.1 | Valid position code | Existing position code | Row validated |
| 2.2.2 | Invalid position code | Non-existent position code | Error file with "Position 'XXX' not found" |
| 2.2.3 | Empty position code | Row with blank position_code | Error file with "Missing position_code" |
| 2.2.4 | Deleted position | Position marked as deleted | Row validated (position exists) |

### 2.3 Serial Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 2.3.1 | Valid serial code | Existing serial code | Row validated |
| 2.3.2 | Invalid serial code | Non-existent serial code | Error file with "Serial 'XXX' not found" |
| 2.3.3 | Deleted serial | Serial with deleted=true | Error file with "Serial 'XXX' not found" |
| 2.3.4 | Serial wrong product | Serial exists but for different product | Error file with "Serial 'XXX' belongs to different product" |

### 2.4 Traceability Validation

| # | Test Case | Product Traceability | Serial Provided | Expected Result |
|---|-----------|---------------------|-----------------|-----------------|
| 2.4.1 | Serialized product with serial | Has traceability_level | Yes | Row validated |
| 2.4.2 | Serialized product without serial | Has traceability_level | No | Error: "Product 'XXX' requires a serial number" |
| 2.4.3 | Non-serialized product without serial | No traceability_level | No | Row validated |
| 2.4.4 | Non-serialized product with serial | No traceability_level | Yes | Error: "Product 'XXX' does not support serial numbers" |

### 2.5 Quantity Validation

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 2.5.1 | Valid integer quantity | `counted_qt = 5` | Row validated |
| 2.5.2 | Valid decimal quantity | `counted_qt = 5.5` | Row validated |
| 2.5.3 | Zero quantity | `counted_qt = 0` | Row validated |
| 2.5.4 | Negative quantity | `counted_qt = -5` | Row validated (or error based on business rules) |
| 2.5.5 | Empty quantity | Blank counted_qt | Error file with "Missing counted_qt" |
| 2.5.6 | Non-numeric quantity | `counted_qt = "abc"` | Error file with "Invalid counted_qt value" |
| 2.5.7 | Serial with qty > 1 | Serial row with `counted_qt = 2` | Should treat as found (qty > 0) |
| 2.5.8 | Serial with qty = 0 | Serial row with `counted_qt = 0` | Serial marked as not found/removed |

---

## 3. Error File Generation

### 3.1 Error File Format

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 3.1.1 | Error file download | File with validation errors | XLSX file downloaded automatically |
| 3.1.2 | Error highlighting | Rows with errors | Error rows highlighted in red |
| 3.1.3 | Status column | All rows | "OK" or "ERROR" in status column |
| 3.1.4 | Error details column | Error rows | Specific error message in errors column |
| 3.1.5 | Multiple errors per row | Row with invalid product AND position | Both errors listed in errors column |

---

## 4. Import Modes

### 4.1 Update Mode

| # | Test Case | Initial State | Import Data | Expected Result |
|---|-----------|---------------|-------------|-----------------|
| 4.1.1 | New product/position | No existing records for pair | Import row | New record created |
| 4.1.2 | Existing record - same pair | Record exists for product/position | Import row for same pair | Existing discarded, new created |
| 4.1.3 | Non-matching records kept | Records for product A/B | Import only product A | Product B records unchanged |
| 4.1.4 | Multiple records same pair | 2 records for same pair | Import 1 row for pair | Both existing discarded, 1 new created |

### 4.2 Replace Mode

| # | Test Case | Initial State | Import Data | Expected Result |
|---|-----------|---------------|-------------|-----------------|
| 4.2.1 | Replace all records | 10 existing records | 5 import rows | All 10 discarded, 5 new created |
| 4.2.2 | Replace with empty | 10 existing records | Empty valid file | All 10 discarded, 0 new created |
| 4.2.3 | Replace confirmation required | Any state | Select replace mode | Checkbox confirmation required before import |
| 4.2.4 | Replace warning shown | Any state | Select replace mode | Warning banner displayed |

---

## 5. Serial Aggregation

### 5.1 Multiple Serial Rows

| # | Test Case | Import Data | Expected Result |
|---|-----------|-------------|-----------------|
| 5.1.1 | Multiple serials same pair | 3 rows: same product/position, different serials, all qty=1 | 1 count record with 3 counted_serial_keys |
| 5.1.2 | Mixed serial quantities | 3 rows: 2 with qty=1, 1 with qty=0 | 1 count record with 2 counted_serial_keys |
| 5.1.3 | All serials qty=0 | 3 rows: all with qty=0 | 1 count record with empty counted_serial_keys, counted_qt=0 |
| 5.1.4 | Duplicate serial rows | 2 rows with same serial code | Second row's quantity used (or deduplicated) |

### 5.2 Non-Serialized Aggregation

| # | Test Case | Import Data | Expected Result |
|---|-----------|-------------|-----------------|
| 5.2.1 | Multiple qty rows same pair | 2 rows: same product/position, qty=5 and qty=3 | 1 count record with counted_qt=8 |
| 5.2.2 | Mixed serial and qty | Row with serial + row without serial, same pair | Serial logic takes precedence |

---

## 6. System Quantities

### 6.1 System Qt Capture

| # | Test Case | System State | Expected Result |
|---|-----------|--------------|-----------------|
| 6.1.1 | Existing inventory | Product has inventory at position | system_qt reflects current inventory |
| 6.1.2 | No inventory | Product has no inventory at position | system_qt = 0 |
| 6.1.3 | Serialized inventory | Serials exist in inventory | system_serial_keys populated |

---

## 7. Edge Cases

### 7.1 Large Files

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 7.1.1 | Large file (1000 rows) | CSV with 1000 valid rows | All rows processed successfully |
| 7.1.2 | Large file with errors | CSV with 1000 rows, 100 errors | Error file generated with all 100 errors |

### 7.2 Special Characters

| # | Test Case | Input | Expected Result |
|---|-----------|-------|-----------------|
| 7.2.1 | Product code with special chars | Code contains `-`, `_`, `.` | Matched correctly |
| 7.2.2 | Position code with spaces | Code contains spaces | Matched correctly (trimmed) |
| 7.2.3 | Serial with unicode | Serial contains unicode chars | Matched correctly |
| 7.2.4 | Commas in CSV fields | Field contains comma (quoted) | Parsed correctly |

### 7.3 Concurrent Operations

| # | Test Case | Scenario | Expected Result |
|---|-----------|----------|-----------------|
| 7.3.1 | Import during active counting | User counting same position | Import proceeds, may conflict |
| 7.3.2 | Double import | Same file imported twice | Second import discards first import's records |

---

## 8. UI Behavior

### 8.1 Drag and Drop

| # | Test Case | Action | Expected Result |
|---|-----------|--------|-----------------|
| 8.1.1 | Drag file over area | Drag valid file | Area highlights |
| 8.1.2 | Drop valid file | Drop .csv or .xlsx | File selected, name shown |
| 8.1.3 | Drop invalid file | Drop .pdf | Error notification, file rejected |
| 8.1.4 | Click to browse | Click drop area | File picker opens |
| 8.1.5 | Clear selected file | Click X button | File cleared, area reset |

### 8.2 Dialog State

| # | Test Case | State | Expected Result |
|---|-----------|-------|-----------------|
| 8.2.1 | Validate button disabled | No file selected | Button disabled |
| 8.2.2 | Import button after validation | Valid file validated | Import button appears |
| 8.2.3 | Try again after error | Validation returned errors | Try again button appears |
| 8.2.4 | Replace checkbox | Replace mode + validated | Checkbox must be checked to import |
| 8.2.5 | Dialog close resets | Close and reopen dialog | All state reset |

---

## 9. Export/Import Round-Trip

### 9.1 Data Integrity

| # | Test Case | Steps | Expected Result |
|---|-----------|-------|-----------------|
| 9.1.1 | Export then import | Export records, import same file (update mode) | Records unchanged (same data) |
| 9.1.2 | Export, modify, import | Export, change qty, import | Updated quantities reflected |
| 9.1.3 | Serial removed on export | Export shows serial with qty=0 | Import with qty=0 excludes from counted_serials |
| 9.1.4 | Serial added on import | Add new serial row to export | New serial appears in counted_serials |

---

## Sample Test Files

### Valid CSV (simple)
```csv
position_code,product_code,counted_qt
A1,PROD001,10
A2,PROD002,5
A3,PROD003,0
```

### Valid CSV (with serials)
```csv
position_code,product_code,serial_code,counted_qt
A1,PROD001,SN-001,1
A1,PROD001,SN-002,1
A1,PROD001,SN-003,0
A2,PROD002,,5
```

### Invalid CSV (for error testing)
```csv
position_code,product_code,serial_code,counted_qt
INVALID_POS,PROD001,,10
A1,INVALID_PROD,,5
A1,PROD001,INVALID_SERIAL,1
A1,PROD001,,abc
```

### Traceability errors CSV
```csv
position_code,product_code,serial_code,counted_qt
A1,SERIALIZED_PROD,,5
A1,NON_SERIALIZED_PROD,SN-001,1
```
Note: `SERIALIZED_PROD` has traceability_level set, `NON_SERIALIZED_PROD` does not.

