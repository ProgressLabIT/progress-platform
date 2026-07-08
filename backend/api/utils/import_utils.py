"""
Shared utilities for bulk CSV/XLSX import endpoints.

Extracted from events/inventory/count_imported.py so that
both product import (Phase 2) and future import flows can
reuse the same parse / error-file / sanitize / column-detect
helpers without creating a cross-domain import dependency.

Security notes:
  T-02-01 — DoS cap: MAX_IMPORT_BYTES / MAX_IMPORT_ROWS enforced at parse entry.
  T-02-02 — Formula injection: _sanitize_cell prefixes leading =, +, -, @ with a
             single quote so xlsx output cannot execute formulas in user spreadsheets.
"""

import csv
import io
import logging

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

logger = logging.getLogger(__name__)

# ============================================================
# SECURITY CONSTANTS (T-02-01)
# ============================================================

MAX_IMPORT_BYTES: int = 10_000_000   # 10 MB
MAX_IMPORT_ROWS: int = 50_000

# ============================================================
# STYLE CONSTANTS
# ============================================================

ERROR_FILL = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
ERROR_FONT = Font(color='CC0000')


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _sanitize_cell(value: str) -> str:
    """
    Neutralise spreadsheet formula-injection in a cell value (T-02-02).

    If the stringified value starts with '=', '+', '-', or '@' — all
    characters Excel / LibreOffice treat as formula triggers — prefix it
    with a literal single-quote so the spreadsheet renders it as text.
    """
    if value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value


def _cell_value_to_string(value) -> str:
    """
    Convert a cell value to string, handling numeric codes correctly.

    Excel stores numeric-looking codes (like "12345") as floats (12345.0).
    This function converts them back to clean strings without the ".0" suffix.
    """
    if value is None:
        return ''
    if isinstance(value, float):
        # Check if it's a whole number (no decimal part)
        if value.is_integer():
            return str(int(value))
        return str(value)
    return str(value).strip()


def _parse_import_file(file_content: bytes, filename: str) -> list[dict]:
    """
    Parse CSV or XLSX file content to a list of row dicts.

    Security (T-02-01): raises ValueError before parsing if file_content
    exceeds MAX_IMPORT_BYTES.  Row-count cap is checked after parsing CSV
    or after iterating the xlsx (openpyxl read_only streams row-by-row so
    we can cap during iteration).

    Args:
        file_content: Raw file bytes.
        filename:     Original filename (used to detect format).

    Returns:
        List of row dicts with lowercased, stripped column names as keys.

    Raises:
        ValueError: unsupported extension, file too large, or too many rows.
    """
    if len(file_content) > MAX_IMPORT_BYTES:
        raise ValueError(
            f"File is too large ({len(file_content):,} bytes). "
            f"Maximum allowed size is {MAX_IMPORT_BYTES:,} bytes (10 MB)."
        )

    rows: list[dict] = []

    if filename.lower().endswith('.csv'):
        # Parse CSV with BOM-safe UTF-8 decode
        text_content = file_content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text_content))
        for row in reader:
            cleaned_row = {k.strip().lower(): v.strip() if v else '' for k, v in row.items()}
            rows.append(cleaned_row)
            if len(rows) > MAX_IMPORT_ROWS:
                raise ValueError(
                    f"File has too many rows (>{MAX_IMPORT_ROWS:,}). "
                    f"Split the file and import in batches."
                )

    elif filename.lower().endswith(('.xlsx', '.xls')):
        # Parse Excel with read_only + data_only (formulas already evaluated)
        wb = load_workbook(filename=io.BytesIO(file_content), read_only=True, data_only=True)
        ws = wb.active

        # Headers from row 1, lowercased
        headers: list[str] = []
        for cell in ws[1]:
            header = str(cell.value).strip().lower() if cell.value else ''
            headers.append(header)

        # Data rows from row 2 onwards
        for row in ws.iter_rows(min_row=2, values_only=True):
            row_dict: dict = {}
            for idx, value in enumerate(row):
                if idx < len(headers) and headers[idx]:
                    row_dict[headers[idx]] = _cell_value_to_string(value)
            if any(row_dict.values()):   # skip fully-empty rows
                rows.append(row_dict)
                if len(rows) > MAX_IMPORT_ROWS:
                    wb.close()
                    raise ValueError(
                        f"File has too many rows (>{MAX_IMPORT_ROWS:,}). "
                        f"Split the file and import in batches."
                    )

        wb.close()

    else:
        raise ValueError(
            f"Unsupported file format: {filename}. Supported formats: .csv, .xlsx"
        )

    return rows


def _detect_ignored_columns(rows: list[dict], known_columns: list[str]) -> list[str]:
    """
    Detect columns present in the file that are not in the known column set.

    Unlike the counting analog, this function accepts the known column set as
    a parameter (product and counting use different column contracts).

    Args:
        rows:          Parsed rows from _parse_import_file.
        known_columns: List of expected column names (e.g. EXPORT_COLUMNS).

    Returns:
        Sorted list of column names that will be ignored during import.
    """
    if not rows:
        return []

    expected = set(known_columns)
    actual = set(rows[0].keys())
    return sorted(actual - expected)


def _generate_error_file(rows: list[dict], error_rows: list[dict], data_columns: list[str]) -> bytes:
    """
    Generate an annotated Excel file with per-row error highlighting.

    Security (T-02-02): all data cells and error message cells are passed
    through _sanitize_cell to prevent formula injection in the returned xlsx.

    Args:
        rows:         Original parsed rows (all rows, including valid ones).
        error_rows:   Rows with errors (each must have '_row_number' and '_errors').
        data_columns: Ordered list of data column names to include (e.g. EXPORT_COLUMNS).

    Returns:
        Excel file as bytes.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = 'Import Validation'

    # Build error lookup by 1-based row number (row 2 in the xlsx = index 0 in rows)
    error_lookup = {r['_row_number']: r['_errors'] for r in error_rows}

    # Headers
    headers = data_columns + ['status', 'errors']
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=header)

    n_data_cols = len(data_columns)

    # Data rows (xlsx row 2 = rows[0])
    for row_idx, row in enumerate(rows, 2):
        for col_idx, col in enumerate(data_columns, 1):
            raw = str(row.get(col, ''))
            ws.cell(row=row_idx, column=col_idx, value=_sanitize_cell(raw))

        if row_idx in error_lookup:
            ws.cell(row=row_idx, column=n_data_cols + 1, value='ERROR')
            error_msg = '; '.join(error_lookup[row_idx])
            ws.cell(row=row_idx, column=n_data_cols + 2, value=_sanitize_cell(error_msg))
            for col in range(1, n_data_cols + 3):
                ws.cell(row=row_idx, column=col).fill = ERROR_FILL
                ws.cell(row=row_idx, column=col).font = ERROR_FONT
        else:
            ws.cell(row=row_idx, column=n_data_cols + 1, value='OK')

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.read()
