"""Integration tests for Product import/export round-trip fidelity (RTR-01).

Seeds products via the import endpoint (not direct inserts) so edge data
(has_tag, can_use_print_template) is created through the event pipeline.
See RESEARCH Pitfall 3: direct Product inserts skip edge cascade, making the
"original state" ambiguous for round-trip assertion.

Flow for each test:
  1. Seed master data (Tag, PrintTemplate, Counter, Position) via direct insert
     — these have no cascade side-effects.
  2. Build an xlsx covering documented edge cases.
  3. Import via dry_run=True → assert 'valid' → execute (creates products+edges).
  4. GET /product/export → assert 200 + spreadsheetml.
  5. Re-import export bytes via dry_run=True → assert status=='valid'.
  6. Execute re-import.
  7. Assert all 8 Column-Contract fields + has_tag / can_use_print_template
     edge sets match originals (set() comparisons = order-insensitive).
"""

import io

import pytest
from openpyxl import Workbook

pytestmark = pytest.mark.asyncio

# 8-field Column Contract (Phase 1 lock — do NOT reorder without updating RTR-02)
EXPORT_COLUMNS = [
    'code', 'description', 'tags', 'print_templates', 'counter',
    'manage_inventory', 'default_consumption_position', 'default_production_position',
]


# ============================================================
# Helpers (copied from test_product_import.py — copy pattern,
# not conftest, to keep test files self-contained per project convention)
# ============================================================

def _make_xlsx(rows: list[dict], columns: list[str] = EXPORT_COLUMNS) -> bytes:
    """Build an in-memory xlsx with the given column headers and data rows."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Products'
    ws.append(columns)
    for row in rows:
        ws.append([row.get(c, '') for c in columns])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


async def _dry_run(client, auth_headers, content: bytes, filename: str = 'test.xlsx'):
    """POST dry_run=True and return the response."""
    media_type = (
        'text/csv'
        if filename.endswith('.csv')
        else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return await client.post(
        '/product/import',
        files={'file': (filename, content, media_type)},
        data={'dry_run': 'true'},
        headers=auth_headers(),
    )


async def _execute(client, auth_headers, file_key: str):
    """POST dry_run=False with the given file_key and return the response."""
    return await client.post(
        '/product/import',
        data={'dry_run': 'false', 'file_key': file_key},
        headers=auth_headers(),
    )


def _assert_product_fields(db, code: str, expected: dict) -> None:
    """
    Run the RTR assertion AQL for the given product code and compare all
    8 Column-Contract fields against `expected`.

    expected keys:
      description        — exact string (or '' for empty)
      tag_names          — set of tag name strings (order-insensitive)
      tmpl_names         — set of print_template name strings (order-insensitive)
      counter_name       — string or None
      manage_inventory   — bool
      consumption_pos    — position code string or None
      production_pos     — position code string or None
    """
    rows = list(db.aql.execute(
        '''
        FOR p IN Product
          FILTER p.code == @code AND !p.trash
          LET tag_names = (
            FOR e IN has_tag FILTER e._from == p._id
            LET t = DOCUMENT(Tag, e._to) RETURN t.name
          )
          LET tmpl_names = (
            FOR e IN can_use_print_template FILTER e._from == p._id
            LET t = DOCUMENT(PrintTemplate, e._to) RETURN t.name
          )
          LET ctr  = p.counter_key
                     ? DOCUMENT(Counter, p.counter_key).name
                     : null
          LET cpos = p.default_consumption_position_key
                     ? DOCUMENT(Position, p.default_consumption_position_key).code
                     : null
          LET ppos = p.default_production_position_key
                     ? DOCUMENT(Position, p.default_production_position_key).code
                     : null
          RETURN {p, tag_names, tmpl_names, ctr, cpos, ppos}
        ''',
        bind_vars={'code': code},
    ))
    assert len(rows) == 1, (
        f"Expected exactly 1 product with code={code!r}, found {len(rows)}"
    )
    r = rows[0]

    # 1. description (exact string; None and '' treated identically — see RESEARCH CF5)
    actual_desc = r['p'].get('description') or ''
    assert actual_desc == expected['description'], (
        f"[{code}] description mismatch: {actual_desc!r} != {expected['description']!r}"
    )

    # 2. tag_names — order-insensitive (RESEARCH CF5: edge traversal order not guaranteed)
    assert set(r['tag_names']) == expected['tag_names'], (
        f"[{code}] tag_names mismatch: {set(r['tag_names'])} != {expected['tag_names']}"
    )

    # 3. tmpl_names — order-insensitive
    assert set(r['tmpl_names']) == expected['tmpl_names'], (
        f"[{code}] tmpl_names mismatch: {set(r['tmpl_names'])} != {expected['tmpl_names']}"
    )

    # 4. counter name
    assert r['ctr'] == expected['counter_name'], (
        f"[{code}] counter_name mismatch: {r['ctr']!r} != {expected['counter_name']!r}"
    )

    # 5. manage_inventory (bool)
    actual_mi = bool(r['p'].get('manage_inventory'))
    assert actual_mi == expected['manage_inventory'], (
        f"[{code}] manage_inventory mismatch: {actual_mi} != {expected['manage_inventory']}"
    )

    # 6. default_consumption_position
    assert r['cpos'] == expected['consumption_pos'], (
        f"[{code}] consumption_pos mismatch: {r['cpos']!r} != {expected['consumption_pos']!r}"
    )

    # 7. default_production_position
    assert r['ppos'] == expected['production_pos'], (
        f"[{code}] production_pos mismatch: {r['ppos']!r} != {expected['production_pos']!r}"
    )


# ============================================================
# Tests — RTR-01: round-trip fidelity
# ============================================================

async def test_round_trip_full_product(client, auth_headers, db):
    """RTR-01 (full-field product): all 8 Column-Contract fields survive export→re-import.

    Covers:
    - Two tags (order-insensitive set comparison)
    - One print template
    - Counter reference
    - manage_inventory=true
    - Both position references
    - Numeric-looking code ('12345') round-trips as exact string, not float/int
    """
    # --- Seed master data (direct insert — no cascade for Tag/Counter/etc.) ---
    db.collection('Tag').insert({'name': 'rtr-steel'})
    db.collection('Tag').insert({'name': 'rtr-aluminum'})
    db.collection('PrintTemplate').insert({'name': 'rtr-label-a4'})
    db.collection('Counter').insert({'name': 'SN-RTR', 'next_tick': 1})
    db.collection('Position').insert({'code': 'RTR-WH-A'})
    db.collection('Position').insert({'code': 'RTR-WH-B'})

    # Also seed with a purely-numeric code to validate float→string handling
    original_rows = [
        {
            'code': 'RTR-001',
            'description': 'Round-trip test product',
            'tags': 'rtr-steel;rtr-aluminum',
            'print_templates': 'rtr-label-a4',
            'counter': 'SN-RTR',
            'manage_inventory': 'true',
            'default_consumption_position': 'RTR-WH-A',
            'default_production_position': 'RTR-WH-B',
        },
        {
            # Numeric-looking code: tests _cell_value_to_string float→int→str path
            'code': '12345',
            'description': 'Numeric code product',
            'tags': 'rtr-steel',
            'print_templates': '',
            'counter': '',
            'manage_inventory': 'true',
            'default_consumption_position': '',
            'default_production_position': '',
        },
    ]

    # --- Step 1: seed via import endpoint (event pipeline — RESEARCH Pitfall 3) ---
    seed_content = _make_xlsx(original_rows)
    seed_dry = await _dry_run(client, auth_headers, seed_content, filename='seed.xlsx')
    assert seed_dry.status_code == 200, f"Seed dry-run failed: {seed_dry.text}"
    seed_body = seed_dry.json()
    assert seed_body['status'] == 'valid', (
        f"Seed dry-run not valid — check reference data: {seed_body}"
    )
    seed_execute = await _execute(client, auth_headers, seed_body['file_key'])
    assert seed_execute.status_code == 200, f"Seed execute failed: {seed_execute.text}"
    assert seed_execute.json()['detail']['created'] == 2

    # --- Step 2: export ---
    export_resp = await client.get(
        '/product/export',
        params={'format': 'xlsx'},
        headers=auth_headers(),
    )
    assert export_resp.status_code == 200, (
        f"Export failed: {export_resp.status_code} {export_resp.text}"
    )
    assert 'spreadsheetml' in export_resp.headers.get('content-type', ''), (
        f"Unexpected content-type: {export_resp.headers.get('content-type')}"
    )

    # --- Step 3: re-import export bytes (dry-run must be 'valid' — no round-trip loss) ---
    reimport_dry = await _dry_run(
        client, auth_headers, export_resp.content, filename='export.xlsx'
    )
    assert reimport_dry.status_code == 200, (
        f"Re-import dry-run HTTP error: {reimport_dry.text}"
    )
    reimport_body = reimport_dry.json()
    assert reimport_body.get('status') == 'valid', (
        f"Round-trip file has validation errors — serialization divergence detected: "
        f"{reimport_body}"
    )
    reimport_file_key = reimport_body['file_key']

    # --- Step 4: execute re-import ---
    reimport_execute = await _execute(client, auth_headers, reimport_file_key)
    assert reimport_execute.status_code == 200, (
        f"Re-import execute failed: {reimport_execute.text}"
    )
    # Both products already exist and are identical → both skipped (idempotent)
    reimport_detail = reimport_execute.json()['detail']
    assert reimport_detail['created'] == 0, (
        f"Re-import should not create new products (already exist); got {reimport_detail}"
    )

    # --- Step 5: assert all 8 fields preserved for RTR-001 ---
    _assert_product_fields(db, 'RTR-001', {
        'description': 'Round-trip test product',
        'tag_names': {'rtr-steel', 'rtr-aluminum'},   # order-insensitive
        'tmpl_names': {'rtr-label-a4'},
        'counter_name': 'SN-RTR',
        'manage_inventory': True,
        'consumption_pos': 'RTR-WH-A',
        'production_pos': 'RTR-WH-B',
    })

    # --- Step 6: assert numeric-looking code round-trips as exact string ---
    numeric_rows = list(db.aql.execute(
        "FOR p IN Product FILTER p.code == @code AND !p.trash RETURN p",
        bind_vars={'code': '12345'},
    ))
    assert len(numeric_rows) == 1, (
        f"Numeric-code product '12345' not found after round-trip "
        f"(expected code to survive as string, not float/int)"
    )
    assert numeric_rows[0]['code'] == '12345', (
        f"Numeric code diverged: expected '12345' (string), got {numeric_rows[0]['code']!r}"
    )


async def test_round_trip_optional_fields(client, auth_headers, db):
    """RTR-01 (optional/empty fields): manage_inventory=false and empty description round-trip cleanly.

    Covers:
    - manage_inventory='false' round-trips as False (not silently converted)
    - Empty description round-trips without spuriously diverging (None→''→None equivalence)
    - No counter, no positions, no print templates
    """
    # --- Seed a single tag for this test (separate namespace from full-product test) ---
    db.collection('Tag').insert({'name': 'rtr-opt-tag'})

    original_rows = [
        {
            'code': 'RTR-OPT-001',
            'description': '',           # intentionally empty
            'tags': 'rtr-opt-tag',
            'print_templates': '',
            'counter': '',
            'manage_inventory': 'false',  # explicit false
            'default_consumption_position': '',
            'default_production_position': '',
        },
    ]

    # --- Step 1: seed via import endpoint ---
    seed_content = _make_xlsx(original_rows)
    seed_dry = await _dry_run(client, auth_headers, seed_content, filename='seed-opt.xlsx')
    assert seed_dry.status_code == 200, f"Seed dry-run failed: {seed_dry.text}"
    seed_body = seed_dry.json()
    assert seed_body['status'] == 'valid', (
        f"Seed dry-run not valid: {seed_body}"
    )
    seed_execute = await _execute(client, auth_headers, seed_body['file_key'])
    assert seed_execute.status_code == 200, f"Seed execute failed: {seed_execute.text}"
    assert seed_execute.json()['detail']['created'] == 1

    # --- Step 2: export ---
    export_resp = await client.get(
        '/product/export',
        params={'format': 'xlsx'},
        headers=auth_headers(),
    )
    assert export_resp.status_code == 200

    # --- Step 3: re-import dry-run must be 'valid' ---
    reimport_dry = await _dry_run(
        client, auth_headers, export_resp.content, filename='export-opt.xlsx'
    )
    assert reimport_dry.status_code == 200, (
        f"Re-import dry-run failed: {reimport_dry.text}"
    )
    reimport_body = reimport_dry.json()
    assert reimport_body.get('status') == 'valid', (
        f"Round-trip file invalid for optional-fields product: {reimport_body}"
    )

    # --- Step 4: execute re-import ---
    reimport_execute = await _execute(client, auth_headers, reimport_body['file_key'])
    assert reimport_execute.status_code == 200, (
        f"Re-import execute failed: {reimport_execute.text}"
    )
    reimport_detail = reimport_execute.json()['detail']
    assert reimport_detail['created'] == 0, (
        f"Re-import should not create new products; got {reimport_detail}"
    )

    # --- Step 5: assert all 8 fields preserved ---
    _assert_product_fields(db, 'RTR-OPT-001', {
        'description': '',             # empty description must stay empty, not None
        'tag_names': {'rtr-opt-tag'},
        'tmpl_names': set(),           # no print templates
        'counter_name': None,          # no counter
        'manage_inventory': False,     # explicit false must survive
        'consumption_pos': None,       # no position
        'production_pos': None,        # no position
    })
