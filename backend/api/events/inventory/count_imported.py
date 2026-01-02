"""
COUNT_IMPORTED event for bulk importing count records from CSV/XLSX files.

This module contains both the event class and utility functions for:
- Parsing import files (CSV/XLSX)
- Validating import rows (bulk lookup of product/position/serial codes)
- Generating error files with annotations
"""

import csv
import io
from enum import Enum
from typing import BinaryIO

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from pydantic import Field

from events.base_event import BaseEvent
from events.inventory.count_discarded import CountDiscardedEvent
from models.event import EventInfoModel, EventType
from models.inventory.counting import InventoryCountRecord, InventoryCountStatus
from utils.dt import timestamp


# ============================================================
# CONSTANTS
# ============================================================

REQUIRED_COLUMNS = ['position_code', 'product_code', 'counted_qt']
# Only serial_code is processed from optional columns.
# System quantities are always fetched from the database, not imported.
OPTIONAL_COLUMNS = ['serial_code']
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS

ERROR_FILL = PatternFill(start_color='FFCCCC', end_color='FFCCCC', fill_type='solid')
ERROR_FONT = Font(color='CC0000')


class ImportMode(str, Enum):
  UPDATE = 'update'
  REPLACE = 'replace'


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def _parse_import_file(file_content: bytes, filename: str) -> list[dict]:
  """
  Parse CSV or XLSX file content to list of dicts.

  Args:
    file_content: Raw file bytes
    filename: Original filename (used to detect format)

  Returns:
    List of row dicts with column names as keys
  """
  rows = []

  if filename.lower().endswith('.csv'):
    # Parse CSV
    text_content = file_content.decode('utf-8-sig')  # Handle  (byte-order mark)
    reader = csv.DictReader(io.StringIO(text_content))
    for row in reader:
      # Clean up keys (strip whitespace, lowercase)
      cleaned_row = {k.strip().lower(): v.strip() if v else '' for k, v in row.items()}
      rows.append(cleaned_row)

  elif filename.lower().endswith(('.xlsx', '.xls')):
    # Parse Excel
    wb = load_workbook(filename=io.BytesIO(file_content), read_only=True, data_only=True)
    ws = wb.active

    # Get headers from first row
    headers = []
    for cell in ws[1]:
      header = str(cell.value).strip().lower() if cell.value else ''
      headers.append(header)

    # Parse data rows
    for row in ws.iter_rows(min_row=2, values_only=True):
      row_dict = {}
      for idx, value in enumerate(row):
        if idx < len(headers) and headers[idx]:
          row_dict[headers[idx]] = str(value).strip() if value is not None else ''
      if any(row_dict.values()):  # Skip empty rows
        rows.append(row_dict)

    wb.close()

  else:
    raise ValueError(f"Unsupported file format: {filename}. Supported formats: .csv, .xlsx")

  return rows


def _validate_columns(rows: list[dict]) -> list[str]:
  """
  Validate that required columns are present.

  Returns:
    List of missing column names (empty if all required columns present)
  """
  if not rows:
    return ['No data rows found in file']

  first_row_keys = set(rows[0].keys())
  missing = []
  for col in REQUIRED_COLUMNS:
    if col not in first_row_keys:
      missing.append(col)
  return missing


def _detect_ignored_columns(rows: list[dict]) -> list[str]:
  """
  Detect columns in the import file that will be ignored.

  System quantities and serials are always fetched from the database,
  so columns like 'system_qt', 'delta', 'username', 'counted_at' are ignored.

  Returns:
    List of column names that are present but will be ignored
  """
  if not rows:
    return []

  expected_columns = set(ALL_COLUMNS)
  actual_columns = set(rows[0].keys())
  ignored = sorted(actual_columns - expected_columns)
  return ignored


def _validate_import_rows(tx, rows: list[dict], session_key: str) -> tuple[list[dict], list[dict]]:
  """
  Bulk validate all import rows by looking up product/position/serial codes.

  Args:
    tx: Database transaction
    rows: List of parsed row dicts
    session_key: Count session key for context

  Returns:
    Tuple of (valid_rows, error_rows)
    - valid_rows: List of dicts with resolved keys added
    - error_rows: List of dicts with 'error' field added
  """
  if not rows:
    return [], []

  # Collect unique codes for bulk lookup
  product_codes = set()
  position_codes = set()
  serial_codes = set()

  for row in rows:
    product_codes.add(row.get('product_code', ''))
    position_codes.add(row.get('position_code', ''))
    if row.get('serial_code'):
      serial_codes.add(row.get('serial_code'))

  # Remove empty strings
  product_codes.discard('')
  position_codes.discard('')

  # Bulk lookup products (including traceability_level)
  # Returns: { product_code: { key, traceability_level } }
  product_lookup = {}
  if product_codes:
    product_lookup = tx.aql.execute('''
      RETURN MERGE(
        FOR p IN Product
        FILTER p.code IN @codes
        RETURN { [p.code]: { key: p._key, traceability_level: p.traceability_level } }
      )
    ''', bind_vars={'codes': list(product_codes)}).next()

  # Bulk lookup positions
  # Returns: { position_code: position_key }
  position_lookup = {}
  if position_codes:
    position_lookup = tx.aql.execute('''
      RETURN MERGE(
        FOR p IN Position
        FILTER p.code IN @codes
        RETURN { [p.code]: p._key }
      )
    ''', bind_vars={'codes': list(position_codes)}).next()

  # Bulk lookup serials by product_code and serial_code
  # Returns: { product_code: { serial_code: serial_key } }
  serial_lookup = {}
  if serial_codes:
    serial_lookup = tx.aql.execute('''
      RETURN MERGE(
        FOR p IN Product
        FILTER p.code IN @product_codes
        LET product_serials = MERGE(
          FOR s IN Serial
          FILTER s.product_key == p._key AND !s.deleted AND s.code IN @serial_codes
          RETURN { [s.code]: s._key }
        )
        RETURN { [p.code]: product_serials }
      )
    ''', bind_vars={'product_codes': list(product_codes), 'serial_codes': list(serial_codes)}).next()

  # Validate each row
  valid_rows = []
  error_rows = []

  for idx, row in enumerate(rows):
    errors = []
    row_with_keys = dict(row)
    row_with_keys['_row_number'] = idx + 2  # Excel row number (1-indexed + header)

    # Check product
    product_code = row.get('product_code', '')
    product_info = None
    if not product_code:
      errors.append('Missing product_code')
    elif product_code not in product_lookup:
      errors.append(f"Product '{product_code}' not found")
    else:
      product_info = product_lookup[product_code]
      row_with_keys['product_key'] = product_info['key']
      row_with_keys['_traceability_level'] = product_info.get('traceability_level')

    # Check position
    position_code = row.get('position_code', '')
    if not position_code:
      errors.append('Missing position_code')
    elif position_code not in position_lookup:
      errors.append(f"Position '{position_code}' not found")
    else:
      row_with_keys['position_key'] = position_lookup[position_code]

    # Check serial and traceability compatibility
    serial_code = row.get('serial_code', '')
    has_traceability = product_info and product_info.get('traceability_level')


    if serial_code:
      # Serial provided - check if product supports traceability
      if product_info and not has_traceability:
        errors.append(f"Product '{product_code}' does not support serial numbers")
      else:
        # Look up serial by product_code first, then serial_code
        serial_key = serial_lookup.get(product_code, {}).get(serial_code)
        if not serial_key:
          errors.append(f"Serial '{serial_code}' not found for product '{product_code}'")
        else:
          row_with_keys['serial_key'] = serial_key
    else:
      # No serial provided - check if product requires traceability
      if has_traceability:
        errors.append(f"Product '{product_code}' requires a serial number")

    # Check counted_qt is a valid number
    counted_qt_str = row.get('counted_qt', '')
    if not counted_qt_str:
      errors.append('Missing counted_qt')
    else:
      try:
        row_with_keys['counted_qt_parsed'] = float(counted_qt_str)
      except ValueError:
        errors.append(f"Invalid counted_qt value: '{counted_qt_str}'")

    if errors:
      row_with_keys['_errors'] = errors
      error_rows.append(row_with_keys)
    else:
      valid_rows.append(row_with_keys)

  return valid_rows, error_rows


def _generate_error_file(rows: list[dict], error_rows: list[dict]) -> bytes:
  """
  Generate an annotated Excel file with error highlighting.

  Args:
    rows: Original parsed rows
    error_rows: Rows with errors (containing '_errors' and '_row_number')

  Returns:
    Excel file as bytes
  """
  wb = Workbook()
  ws = wb.active
  ws.title = 'Import Validation'

  # Build error lookup by row number
  error_lookup = {r['_row_number']: r['_errors'] for r in error_rows}

  # Write headers
  headers = REQUIRED_COLUMNS + ['serial_code'] + ['status', 'errors']
  for col_idx, header in enumerate(headers, 1):
    ws.cell(row=1, column=col_idx, value=header)

  # Write data rows
  for row_idx, row in enumerate(rows, 2):
    # Write original data
    ws.cell(row=row_idx, column=1, value=row.get('position_code', ''))
    ws.cell(row=row_idx, column=2, value=row.get('product_code', ''))
    ws.cell(row=row_idx, column=3, value=row.get('counted_qt', ''))
    ws.cell(row=row_idx, column=4, value=row.get('serial_code', ''))

    # Write status and errors
    if row_idx in error_lookup:
      ws.cell(row=row_idx, column=5, value='ERROR')
      ws.cell(row=row_idx, column=6, value='; '.join(error_lookup[row_idx]))
      # Apply error styling
      for col in range(1, 7):
        cell = ws.cell(row=row_idx, column=col)
        cell.fill = ERROR_FILL
        cell.font = ERROR_FONT
    else:
      ws.cell(row=row_idx, column=5, value='OK')

  # Auto-size columns (approximate)
  for col_idx, header in enumerate(headers, 1):
    ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = max(len(header) + 2, 15)

  # Save to bytes
  output = io.BytesIO()
  wb.save(output)
  output.seek(0)
  return output.read()


def _aggregate_rows_by_product_position(valid_rows: list[dict]) -> dict:
  """
  Aggregate import rows by product+position combination.
  For serialized products, collect serial keys.

  Returns:
    Dict keyed by (product_key, position_key) with aggregated data
  """
  aggregated = {}

  for row in valid_rows:
    key = (row['product_key'], row['position_key'])

    if key not in aggregated:
      aggregated[key] = {
        'product_key': row['product_key'],
        'position_key': row['position_key'],
        'product_code': row.get('product_code'),
        'position_code': row.get('position_code'),
        'counted_qt': 0.0,
        'serial_keys': [],
      }

    counted_qt = row.get('counted_qt_parsed', 0.0)

    if row.get('serial_key'):
      # Serialized row: add serial if counted_qt > 0
      if counted_qt > 0:
        aggregated[key]['serial_keys'].append(row['serial_key'])
      # Don't add to counted_qt - it will be derived from serial count
    else:
      # Non-serialized: sum quantities
      aggregated[key]['counted_qt'] += counted_qt

  # For serialized products, set counted_qt from serial count
  for agg in aggregated.values():
    if agg['serial_keys']:
      agg['counted_qt'] = len(agg['serial_keys'])

  return aggregated


# ============================================================
# EVENT CLASS
# ============================================================

class CountImportedEvent(BaseEvent):
  """
  Event for importing count records from an uploaded file.

  The file must already be stored in media storage before this event is triggered.
  """

  class InfoModel(EventInfoModel):
    count_session_key: str
    import_mode: str = Field(..., description="'update' or 'replace'")
    import_file_key: str = Field(..., description="Media storage key of the uploaded file")
    import_filename: str = Field(..., description="Original filename for format detection")
    # Summary stats (populated during apply)
    rows_total: int = 0
    rows_added: int = 0
    rows_updated: int = 0
    rows_discarded: int = 0
    ignored_columns: list[str] = Field(default_factory=list, description="Columns in file that were ignored")

  @classmethod
  def get_event_type(cls):
    return EventType.COUNT_IMPORTED

  @classmethod
  def get_tx_collections(cls):
    return ['inventory_count_record', 'Product', 'Position', 'Serial', 'is_in_position']

  def apply(self):
    # Verify file metadata first (security check)
    metadata = self._verify_file_metadata()

    # Read file from media storage
    file_content = self._read_file_from_media()

    # Parse file
    rows = _parse_import_file(file_content, self.info.import_filename)
    self.info.rows_total = len(rows)

    # Detect ignored columns and store warning
    self.info.ignored_columns = _detect_ignored_columns(rows)

    # Validate rows (re-validation for safety, but should pass since endpoint validated)
    valid_rows, error_rows = _validate_import_rows(self.tx, rows, self.info.count_session_key)

    if error_rows:
      raise ValueError(
        f"Import validation failed: {len(error_rows)} rows have errors. "
        f"Use the import endpoint with dry_run=True first to get detailed error report."
      )

    # Aggregate rows by product/position
    aggregated = _aggregate_rows_by_product_position(valid_rows)

    # Handle import mode
    if self.info.import_mode == ImportMode.REPLACE:
      self._discard_all_session_records()

    # Process each aggregated record
    for (product_key, position_key), data in aggregated.items():
      if self.info.import_mode == ImportMode.UPDATE:
        # Discard existing records for this product/position
        discarded = self._discard_matching_records(product_key, position_key)
        self.info.rows_discarded += discarded

      # Create new count record
      self._create_count_record(data)
      self.info.rows_added += 1

    self.response = {
      'message': f"Successfully imported {self.info.rows_added} count records",
      'rows_total': self.info.rows_total,
      'rows_added': self.info.rows_added,
      'rows_discarded': self.info.rows_discarded,
    }

    # Add warning about ignored columns if any
    if self.info.ignored_columns:
      self.response['warnings'] = [
        f"The following columns were ignored (system quantities are fetched from database): {', '.join(self.info.ignored_columns)}"
      ]

  def _verify_file_metadata(self) -> dict:
    """
    Verify file metadata for security.

    Checks:
    - Metadata file exists
    - File was validated (validated=True)
    - File was validated for this session (session_key matches)

    Returns:
      The metadata dict if valid

    Raises:
      ValueError if validation fails
    """
    import json
    import os

    media_path = os.environ.get('MEDIA_PATH', '/app/media')
    meta_path = os.path.join(media_path, 'count_import', f'{self.info.import_file_key}.meta.json')

    if not os.path.exists(meta_path):
      raise ValueError(
        f"File metadata not found for: {self.info.import_file_key}. "
        f"Use the import endpoint with dry_run=True to validate the file first."
      )

    with open(meta_path, 'r') as f:
      metadata = json.load(f)

    if not metadata.get('validated'):
      raise ValueError(
        f"File was not validated. Use the import endpoint with dry_run=True first."
      )

    if metadata.get('session_key') != self.info.count_session_key:
      raise ValueError(
        f"File was validated for a different session. "
        f"Expected session: {metadata.get('session_key')}, got: {self.info.count_session_key}"
      )

    return metadata

  def _read_file_from_media(self) -> bytes:
    """Read the import file from media storage."""
    import os
    media_path = os.environ.get('MEDIA_PATH', '/app/media')
    file_path = os.path.join(media_path, 'count_import', self.info.import_file_key)

    if not os.path.exists(file_path):
      raise ValueError(f"Import file not found: {self.info.import_file_key}")

    with open(file_path, 'rb') as f:
      return f.read()

  def _discard_all_session_records(self):
    """Discard all existing count records for the session (replace mode)."""
    cursor = self.tx.aql.execute('''
      FOR r IN inventory_count_record
      FILTER r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted', 'confirmed']
      RETURN r._key
    ''', bind_vars={'session_key': self.info.count_session_key})

    for record_key in cursor:
      CountDiscardedEvent.create_as_child(self, {'count_key': record_key})
      self.info.rows_discarded += 1

  def _discard_matching_records(self, product_key: str, position_key: str) -> int:
    """Discard existing records matching product/position (update mode)."""
    cursor = self.tx.aql.execute('''
      FOR r IN inventory_count_record
      FILTER r._from == @product_id
        AND r._to == @position_id
        AND r.inventory_count_session_key == @session_key
        AND r.status IN ['completed', 'submitted', 'confirmed']
      RETURN r._key
    ''', bind_vars={
      'product_id': f'Product/{product_key}',
      'position_id': f'Position/{position_key}',
      'session_key': self.info.count_session_key,
    })

    discarded = 0
    for record_key in cursor:
      CountDiscardedEvent.create_as_child(self, {'count_key': record_key})
      discarded += 1

    return discarded

  def _create_count_record(self, data: dict):
    """Create a new count record from aggregated import data."""
    # Get system quantities for this product/position
    system_qt, system_serial_keys = self._get_system_quantities(
      data['product_key'],
      data['position_key']
    )

    count_record = InventoryCountRecord(
      product_id=f"Product/{data['product_key']}",
      position_id=f"Position/{data['position_key']}",
      system_qt=system_qt,
      system_serial_keys=system_serial_keys if system_serial_keys else None,
      system_at=timestamp(),
      counted_qt=data['counted_qt'],
      counted_serial_keys=data['serial_keys'] if data['serial_keys'] else None,
      counted_at=self.info.timestamp,
      user_key=self.info.user_key,
      inventory_count_session_key=self.info.count_session_key,
      status=InventoryCountStatus.COMPLETED,
    )

    self.tx.collection('inventory_count_record').insert(
      count_record.model_dump(by_alias=True)
    )

  def _get_system_quantities(self, product_key: str, position_key: str) -> tuple[float, list[str]]:
    """Get current system quantities and serials for a product/position."""
    cursor = self.tx.aql.execute('''
      FOR i IN is_in_position
      FILTER i._from == @product_id AND i._to == @position_id
      RETURN { quantity: i.quantity, serial_key: i.serial_key }
    ''', bind_vars={
      'product_id': f'Product/{product_key}',
      'position_id': f'Position/{position_key}',
    })

    total_qt = 0.0
    serial_keys = []
    for inv in cursor:
      total_qt += inv.get('quantity', 0) or 0
      if inv.get('serial_key'):
        serial_keys.append(inv['serial_key'])

    return total_qt, serial_keys

