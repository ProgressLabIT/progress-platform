"""
PRODUCT_IMPORTED event — batch import of products from a validated CSV/XLSX file.

Plan 01 (create-only) is extended in Plan 02 to add idempotent upsert semantics:
  - IMP-04: match existing product by `code`, update in place (code never mutated).
  - IMP-06 / D-02: re-importing an unchanged file produces zero writes (per-product diff
    including order-insensitive edge sets).
  - D-01 (empty-cell authoritative): column PRESENT in file is authoritative; empty cell
    clears the field. Column ABSENT from file leaves that field untouched.

Security notes:
  T-02-03 — Reference-resolution AQL: all user-supplied name/code values travel
             exclusively as AQL bind vars, never string-interpolated into queries.
  T-02-04 — file_key validation: _verify_file_metadata() requires an on-disk
             .meta.json sidecar with validated=true; a forged or un-validated key
             raises ValueError → the BaseEvent finally block aborts the transaction.
  T-02-07 — _fetch_existing and edge REMOVE AQL use bind vars only; `code` and
             `Product/<key>` are never string-interpolated.
  T-02-08 — Edge REMOVE is scoped to `_from == @prod_id` — only the target product's
             edges are affected; other products' edges cannot be deleted.
"""

import json
import logging
import os

from pydantic import Field

from events.base_event import BaseEvent
from models.event import EventInfoModel, EventType
from utils.config import get_config
from utils.dt import timestamp
from utils.import_utils import _parse_import_file

logger = logging.getLogger(__name__)

# Sub-directory under MEDIA_PATH used by product import
_PRODUCT_IMPORT_SUBDIR = 'product_import'

# Sentinel used to distinguish "column absent from file" from "column present but empty".
# An absent column contributes this sentinel in the resolved dict so _is_identical can
# treat it as "no change" by substituting the existing value before comparing.
_ABSENT = object()


class ProductImportedEvent(BaseEvent):
    """
    Batch-import event: reads a validated file from media storage, resolves
    all 4 reference types (Tag, PrintTemplate, Counter, Position) via bulk AQL,
    then creates, updates, or skips each Product inside the event transaction.

    Create/update/skip semantics (Plan 02):
      - new code → create (Plan-01 path).
      - existing code, identical state → skip (no write, no event side-effect).
      - existing code, changed state → update in place; code field never mutated.

    The event intentionally sets _notification_subtopic = None — ProductList.vue
    refreshes via the dialog's @imported emit (L-3 / RESEARCH §8).
    """

    _notification_subtopic = None  # No NATS publish (L-3)

    class InfoModel(EventInfoModel):
        import_file_key: str = Field(..., description="Media storage key of the validated file")
        import_filename: str = Field(..., description="Original filename (for format detection)")
        rows_total: int = 0
        rows_created: int = 0
        rows_updated: int = 0
        rows_skipped: int = 0

    @classmethod
    def get_event_type(cls):
        return EventType.PRODUCT_IMPORTED

    @classmethod
    def get_tx_collections(cls):
        # BaseEvent.save() appends ['Event', 'event_source'] automatically.
        return [
            'Product',
            'Tag', 'has_tag',
            'PrintTemplate', 'can_use_print_template',
            'Counter',
            'Position',
        ]

    # ------------------------------------------------------------------ #
    # Public entry point                                                   #
    # ------------------------------------------------------------------ #

    def apply(self):
        # 1. Security: verify the file was produced by a validated dry-run call
        self._verify_file_metadata()

        # 2. Read the raw bytes from media storage
        file_content = self._read_file_from_media()

        # 3. Parse
        rows = _parse_import_file(file_content, self.info.import_filename)
        self.info.rows_total = len(rows)

        # 4. Bulk reference resolution (all 4 types in one pass; T-02-03)
        tag_lookup, tmpl_lookup, counter_lookup, pos_lookup = self._resolve_product_refs(rows)

        # 5. First pass: validate all rows — block-all on any error (D-03)
        error_rows: list[dict] = []
        for row_number, row in enumerate(rows, start=1):
            resolved, row_errors = self._resolve_row(
                row, row_number, tag_lookup, tmpl_lookup, counter_lookup, pos_lookup
            )
            if row_errors:
                error_rows.append({'_row_number': row_number, '_errors': row_errors})

        if error_rows:
            # Block-all: any unresolved reference rolls back the entire transaction (D-03)
            n = len(error_rows)
            raise ValueError(
                f"Import validation failed: {n} row(s) have errors. "
                f"Use the import endpoint with dry_run=True first to get the annotated error file."
            )

        # 6. All rows are valid — upsert: create / update / skip per row (IMP-04, IMP-06)
        current_time = str(timestamp())
        for row_number, row in enumerate(rows, start=1):
            resolved, _ = self._resolve_row(
                row, row_number, tag_lookup, tmpl_lookup, counter_lookup, pos_lookup
            )

            existing = self._fetch_existing(resolved['code'])

            if existing is None:
                # New product — create (Plan-01 path)
                self._create_product(resolved, current_time)
                self.info.rows_created += 1
            elif self._is_identical(existing, resolved):
                # Identical to current state — skip (D-02 no-op)
                self.info.rows_skipped += 1
            else:
                # Changed — update in place (IMP-04)
                self._update_product(existing['key'], resolved, current_time)
                self.info.rows_updated += 1

        self.response = {
            'created': self.info.rows_created,
            'updated': self.info.rows_updated,
            'skipped': self.info.rows_skipped,
            'total': self.info.rows_total,
        }

    # ------------------------------------------------------------------ #
    # Reference resolution                                                 #
    # ------------------------------------------------------------------ #

    def _resolve_product_refs(
        self,
        rows: list[dict],
    ) -> tuple[dict, dict, dict, dict]:
        """
        Bulk-resolve all 4 reference types for the given rows.

        Security (T-02-03): user values travel only via AQL bind vars.

        Returns:
            (tag_lookup, tmpl_lookup, counter_lookup, pos_lookup)
            Each is a dict mapping name/code → ArangoDB _key string.
        """
        all_tag_names: set[str] = set()
        all_tmpl_names: set[str] = set()
        all_counter_names: set[str] = set()
        all_pos_codes: set[str] = set()

        for row in rows:
            for name in (row.get('tags') or '').split(';'):
                if n := name.strip():
                    all_tag_names.add(n)
            for name in (row.get('print_templates') or '').split(';'):
                if n := name.strip():
                    all_tmpl_names.add(n)
            if c := (row.get('counter') or '').strip():
                all_counter_names.add(c)
            if p := (row.get('default_consumption_position') or '').strip():
                all_pos_codes.add(p)
            if p := (row.get('default_production_position') or '').strip():
                all_pos_codes.add(p)

        def _bulk_lookup(collection: str, field: str, values: set[str]) -> dict:
            """One RETURN MERGE query per ref type (T-02-03: bind vars only)."""
            if not values:
                return {}
            result = self.tx.aql.execute(
                f'RETURN MERGE(FOR doc IN {collection} FILTER doc.{field} IN @vals'
                f' RETURN {{ [doc.{field}]: doc._key }})',
                bind_vars={'vals': list(values)}
            ).next()
            return result or {}

        return (
            _bulk_lookup('Tag', 'name', all_tag_names),
            _bulk_lookup('PrintTemplate', 'name', all_tmpl_names),
            _bulk_lookup('Counter', 'name', all_counter_names),
            _bulk_lookup('Position', 'code', all_pos_codes),
        )

    def _resolve_row(
        self,
        row: dict,
        row_number: int,
        tag_lookup: dict,
        tmpl_lookup: dict,
        counter_lookup: dict,
        pos_lookup: dict,
    ) -> tuple[dict, list[str]]:
        """
        Resolve a single import row into a fully resolved dict or a list of errors.

        Column-presence semantics (D-01):
            - 'code' must be present and non-empty (only required column).
            - All other columns are optional. A column PRESENT in the row dict but
              empty clears that field. A column ABSENT from the row dict gets the
              sentinel _ABSENT, signalling "leave field untouched" on update.

        Returns:
            (resolved_dict, errors_list).  errors_list is empty on success.
        """
        errors: list[str] = []
        resolved: dict = {'_row_number': row_number}

        # --- code (required) ---
        code = (row.get('code') or '').strip()
        if not code:
            errors.append("Missing required value: 'code'")
        else:
            resolved['code'] = code

        # --- description (optional) ---
        if 'description' in row:
            resolved['description'] = (row.get('description') or '').strip()
        else:
            resolved['description'] = _ABSENT

        # --- manage_inventory (optional, bool) ---
        if 'manage_inventory' in row:
            raw = (row.get('manage_inventory') or '').strip().lower()
            if raw and raw not in ('true', 'false'):
                errors.append(f"type-mismatch: 'manage_inventory' must be 'true' or 'false', got '{raw}'")
            else:
                resolved['manage_inventory'] = (raw == 'true')
        else:
            resolved['manage_inventory'] = _ABSENT

        # --- tags (optional, multi-value ';'-split) ---
        if 'tags' in row:
            raw_tags = (row.get('tags') or '').strip()
            tag_ids: list[str] = []
            if raw_tags:
                for name in raw_tags.split(';'):
                    name = name.strip()
                    if not name:
                        continue
                    key = tag_lookup.get(name)
                    if key is None:
                        errors.append(f"Unknown tag: '{name}'")
                    else:
                        tag_ids.append(f'Tag/{key}')
            resolved['tag_ids'] = tag_ids
        else:
            resolved['tag_ids'] = _ABSENT

        # --- print_templates (optional, multi-value ';'-split) ---
        if 'print_templates' in row:
            raw_tmpls = (row.get('print_templates') or '').strip()
            tmpl_ids: list[str] = []
            if raw_tmpls:
                for name in raw_tmpls.split(';'):
                    name = name.strip()
                    if not name:
                        continue
                    key = tmpl_lookup.get(name)
                    if key is None:
                        errors.append(f"Unknown print template: '{name}'")
                    else:
                        tmpl_ids.append(f'PrintTemplate/{key}')
            resolved['tmpl_ids'] = tmpl_ids
        else:
            resolved['tmpl_ids'] = _ABSENT

        # --- counter (optional, resolved by name) ---
        if 'counter' in row:
            raw_counter = (row.get('counter') or '').strip()
            if raw_counter:
                key = counter_lookup.get(raw_counter)
                if key is None:
                    errors.append(f"Unknown counter: '{raw_counter}'")
                else:
                    resolved['counter_key'] = key
            else:
                resolved['counter_key'] = None
        else:
            resolved['counter_key'] = _ABSENT

        # --- default_consumption_position (optional, resolved by code) ---
        if 'default_consumption_position' in row:
            raw_pos = (row.get('default_consumption_position') or '').strip()
            if raw_pos:
                key = pos_lookup.get(raw_pos)
                if key is None:
                    errors.append(f"Unknown position code: '{raw_pos}' (consumption)")
                else:
                    resolved['default_consumption_position_key'] = key
            else:
                resolved['default_consumption_position_key'] = None
        else:
            resolved['default_consumption_position_key'] = _ABSENT

        # --- default_production_position (optional, resolved by code) ---
        if 'default_production_position' in row:
            raw_pos = (row.get('default_production_position') or '').strip()
            if raw_pos:
                key = pos_lookup.get(raw_pos)
                if key is None:
                    errors.append(f"Unknown position code: '{raw_pos}' (production)")
                else:
                    resolved['default_production_position_key'] = key
            else:
                resolved['default_production_position_key'] = None
        else:
            resolved['default_production_position_key'] = _ABSENT

        return resolved, errors

    # ------------------------------------------------------------------ #
    # Upsert helpers (Plan 02)                                            #
    # ------------------------------------------------------------------ #

    def _fetch_existing(self, code: str) -> dict | None:
        """
        Fetch the current Product doc and its edge sets by code (inside self.tx).

        Security (T-02-07): `code` travels as a bind var only.

        Returns a dict with keys: key, description, counter_key, manage_inventory,
        default_consumption_position_key, default_production_position_key,
        tag_set (list of "Tag/<key>"), tmpl_set (list of "PrintTemplate/<key>").
        Returns None if no non-trashed product with this code exists.
        """
        cursor = self.tx.aql.execute(
            '''
            FOR p IN Product
              FILTER p.code == @code AND !p.trash
              LET tag_keys  = (FOR e IN has_tag                FILTER e._from == p._id RETURN e._to)
              LET tmpl_keys = (FOR e IN can_use_print_template FILTER e._from == p._id RETURN e._to)
              RETURN {
                key: p._key,
                description: p.description,
                counter_key: p.counter_key,
                manage_inventory: p.manage_inventory,
                default_consumption_position_key: p.default_consumption_position_key,
                default_production_position_key: p.default_production_position_key,
                tag_set: tag_keys,
                tmpl_set: tmpl_keys
              }
            ''',
            bind_vars={'code': code}
        )
        return next(cursor, None)

    def _is_identical(self, existing: dict, resolved: dict) -> bool:
        """
        Return True if the resolved import row matches current product state exactly.

        D-01 / D-02 semantics:
          - Only columns PRESENT in the file (non-_ABSENT resolved values) are compared.
          - Absent columns are treated as equal to current state (no change intended).
          - Edge sets are compared as Python sets (order-insensitive) per D-02.
          - manage_inventory is coerced to bool on both sides.
        """
        # --- description ---
        resolved_description = resolved['description']
        if resolved_description is not _ABSENT:
            if (existing.get('description') or '') != resolved_description:
                return False

        # --- manage_inventory ---
        resolved_mi = resolved['manage_inventory']
        if resolved_mi is not _ABSENT:
            if bool(existing.get('manage_inventory')) != bool(resolved_mi):
                return False

        # --- counter_key ---
        resolved_ck = resolved['counter_key']
        if resolved_ck is not _ABSENT:
            if existing.get('counter_key') != resolved_ck:
                return False

        # --- default_consumption_position_key ---
        resolved_cpos = resolved['default_consumption_position_key']
        if resolved_cpos is not _ABSENT:
            if existing.get('default_consumption_position_key') != resolved_cpos:
                return False

        # --- default_production_position_key ---
        resolved_ppos = resolved['default_production_position_key']
        if resolved_ppos is not _ABSENT:
            if existing.get('default_production_position_key') != resolved_ppos:
                return False

        # --- tag_set (order-insensitive, D-02) ---
        resolved_tags = resolved['tag_ids']
        if resolved_tags is not _ABSENT:
            if set(existing.get('tag_set') or []) != set(resolved_tags):
                return False

        # --- tmpl_set (order-insensitive, D-02) ---
        resolved_tmpls = resolved['tmpl_ids']
        if resolved_tmpls is not _ABSENT:
            if set(existing.get('tmpl_set') or []) != set(resolved_tmpls):
                return False

        return True

    def _update_product(self, product_key: str, resolved: dict, current_time: str) -> None:
        """
        Update an existing Product doc and sync its edge sets in place (IMP-04).

        D-01 constraints:
          - Only fields whose column was PRESENT in the file are included in the update doc.
          - `code` and `created` are NEVER included in the update.
          - For edge collections: edges are cleared-then-reinserted only if the column was
            PRESENT. Absent edge columns leave existing edges untouched (T-02-08).

        Security (T-02-07): product_id travels as a bind var; no string interpolation.
        """
        product_id = f'Product/{product_key}'
        update_doc: dict = {'updated': current_time}

        # Scalar fields — only include if column was present
        for field in ('description', 'manage_inventory', 'counter_key',
                      'default_consumption_position_key', 'default_production_position_key'):
            val = resolved.get(field)
            if val is not _ABSENT:
                update_doc[field] = val

        # Apply scalar update
        self.tx.collection('Product').update({'_key': product_key, **update_doc})

        # Edge sync: has_tag — only if tags column was present
        resolved_tags = resolved.get('tag_ids')
        if resolved_tags is not _ABSENT:
            # Clear all existing has_tag edges for this product (T-02-08: scoped by _from)
            self.tx.aql.execute(
                'FOR e IN has_tag FILTER e._from == @prod_id REMOVE e IN has_tag',
                bind_vars={'prod_id': product_id}
            )
            # Insert the new set (may be empty — that is the "clear" case for D-01)
            if resolved_tags:
                edges = [{'_from': product_id, '_to': tag_id} for tag_id in resolved_tags]
                self.tx.collection('has_tag').insert_many(edges)

        # Edge sync: can_use_print_template — only if print_templates column was present
        resolved_tmpls = resolved.get('tmpl_ids')
        if resolved_tmpls is not _ABSENT:
            # Clear all existing can_use_print_template edges for this product
            self.tx.aql.execute(
                'FOR e IN can_use_print_template FILTER e._from == @prod_id REMOVE e IN can_use_print_template',
                bind_vars={'prod_id': product_id}
            )
            # Insert the new set (may be empty)
            if resolved_tmpls:
                edges = [{'_from': product_id, '_to': tmpl_id} for tmpl_id in resolved_tmpls]
                self.tx.collection('can_use_print_template').insert_many(edges)

    # ------------------------------------------------------------------ #
    # Write helpers                                                        #
    # ------------------------------------------------------------------ #

    def _create_product(self, resolved: dict, created_time: str) -> str:
        """
        Insert a new Product document and its edge relationships inside self.tx.

        Returns the new product _key.
        """
        doc: dict = {
            'code': resolved['code'],
            'active': True,
            'trash': False,
            'created': created_time,
        }

        # Apply optional columns that were present in the file (exclude _ABSENT sentinels).
        # Explicitly-None values are included (empty cell → None means "clear the field").
        for field in ('description', 'manage_inventory', 'counter_key',
                      'default_consumption_position_key', 'default_production_position_key'):
            val = resolved.get(field, _ABSENT)
            if val is not _ABSENT:
                doc[field] = val

        result = self.tx.collection('Product').insert(doc)
        product_key = result['_key']
        product_id = f'Product/{product_key}'

        # has_tag edges
        tag_ids = resolved.get('tag_ids', _ABSENT)
        if tag_ids is not _ABSENT and tag_ids:
            edges = [{'_from': product_id, '_to': tag_id} for tag_id in tag_ids]
            self.tx.collection('has_tag').insert_many(edges)

        # can_use_print_template edges
        tmpl_ids = resolved.get('tmpl_ids', _ABSENT)
        if tmpl_ids is not _ABSENT and tmpl_ids:
            edges = [{'_from': product_id, '_to': tmpl_id} for tmpl_id in tmpl_ids]
            self.tx.collection('can_use_print_template').insert_many(edges)

        return product_key

    # ------------------------------------------------------------------ #
    # Media / metadata helpers (mirror count_imported.py pattern)         #
    # ------------------------------------------------------------------ #

    def _verify_file_metadata(self) -> dict:
        """
        Verify the .meta.json sidecar written by the dry-run endpoint.

        Security (T-02-04): requires validated=True in the sidecar; a forged or
        un-validated file_key raises ValueError → BaseEvent finally aborts the tx.
        Product import has no session_key — that check is intentionally omitted.

        Returns:
            The metadata dict.
        """
        media_path = get_config().media_path
        meta_path = os.path.join(
            media_path, _PRODUCT_IMPORT_SUBDIR, f'{self.info.import_file_key}.meta.json'
        )

        if not os.path.exists(meta_path):
            raise ValueError(
                f"File metadata not found for: {self.info.import_file_key}. "
                f"Use the import endpoint with dry_run=True to validate the file first."
            )

        with open(meta_path, 'r') as f:
            metadata = json.load(f)

        if not metadata.get('validated'):
            raise ValueError(
                "File was not validated. Use the import endpoint with dry_run=True first."
            )

        return metadata

    def _read_file_from_media(self) -> bytes:
        """Read the validated import file bytes from media storage."""
        media_path = get_config().media_path
        file_path = os.path.join(
            media_path, _PRODUCT_IMPORT_SUBDIR, self.info.import_file_key
        )

        if not os.path.exists(file_path):
            raise ValueError(f"Import file not found: {self.info.import_file_key}")

        with open(file_path, 'rb') as f:
            return f.read()
