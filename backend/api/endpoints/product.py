import csv
import io
import json
import os
import traceback
import uuid
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Form, File, HTTPException, UploadFile, Body, Query, Depends
from fastapi.responses import Response
from openpyxl import Workbook
from utils import auth
from fastapi.encoders import jsonable_encoder

from events.product.product_imported import ProductImportedEvent
from models.event import EventInfoModel
from utils.import_utils import _parse_import_file, _detect_ignored_columns, _generate_error_file

from utils.kpi import Queries as ProductStatQueries
from models.product import *
from models.process import PhaseData
from utils.api import APIResponse
from utils.config import get_config
from utils.db import db
from utils.dt import timestamp
from utils.file import FileHandler
from utils.product import *
from utils.process import Queries as ProcessQueries, copy_process_to_product, copy_process_to_product_writes

router = APIRouter()

product_db = db.collection('Product')


# ALL ROUTES BEGIN WITH 'product'

# =================================================
#  GET / : GET PRODUCT LIST
# =================================================
@router.get("",
    response_model=list,
    responses={500: {"description": "Database query error"}},
    dependencies=[Depends(auth.verify_token)])
async def get_product_list(params: Annotated[ProductSearchParams, Query()]):
  """List products with optional filtering and search.

  Accepts `ProductSearchParams` as query parameters. When `details=false`
  (default), returns lightweight `ProductBaseData` objects; when `details=true`,
  returns full `ProductDetails` including cost, process phases, and metadata.

  Supports full-text search, tag inclusion/exclusion filters, traceability
  filtering, and pagination via `limit`/`offset`.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `product:catalogue:read`
  """
  print(params.model_dump())
  product_list =  db.aql.execute(
    Queries.GET_PRODUCT_LIST,
    bind_vars=params.model_dump(),
  )

  def validate(data):
    return ProductDetails(**data) if params.details else ProductBaseData(**data)

  results = [validate(product) for product in product_list]
  return results


# =================================================
#  GET /export : EXPORT PRODUCT CATALOG
# =================================================
@router.get(
    "/export",
    dependencies=[Depends(auth.verify_token)],
    responses={
        200: {
            "content": {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/csv": {},
            }
        }
    },
)
async def export_products(
    # NOTE: Depends() (not Query()) is required here. FastAPI flattens a
    # Pydantic-model query param annotated with Query() ONLY when it is the
    # sole parameter; combined with the extra `format` scalar below it stops
    # flattening and 422s on a missing `params` field. Depends() flattens
    # regardless. The list endpoint above can use Query() because the model
    # is its only parameter.
    params: Annotated[ProductSearchParams, Depends()],
    format: Literal["xlsx", "csv", "template"] = "xlsx",
):
    """Export the product catalog to xlsx, CSV, or a header-only template file.

    Accepts the same ProductSearchParams filters as GET /product. Pagination
    (limit/offset) is ignored — export always returns all matching records.

    Formats:
    - xlsx (default): Excel workbook with 8-column contract header row
    - csv: CSV with same 8-column header row, BOM-prefixed for Excel compat
    - template: Header-only xlsx with no data rows (for import preparation)

    **Required scope:** product:catalogue:read
    """
    # Override pagination — export always returns all matching records
    params.limit = None
    params.offset = 0

    if format == "template":
        rows = []
    else:
        # Same filter contract as get_product_list, minus `details`: the list
        # query references @details in its RETURN (ProductDetails vs ProductBaseData),
        # but EXPORT_PRODUCT has a fixed 8-column RETURN that never uses it. ArangoDB
        # rejects any bind var the query doesn't reference (ERR 1552), so drop it.
        # limit/offset already nulled above, so @limit || null returns everything.
        bind_vars = params.model_dump()
        bind_vars.pop("details", None)
        raw_rows = list(db.aql.execute(Queries.EXPORT_PRODUCT, bind_vars=bind_vars))
        rows = []
        for row in raw_rows:
            rows.append({
                **row,
                "tags": ";".join(row.get("tags") or []),
                "print_templates": ";".join(row.get("print_templates") or []),
                "counter": row.get("counter") or "",
                "manage_inventory": "true" if row.get("manage_inventory") else "false",
                "default_consumption_position": row.get("default_consumption_position") or "",
                "default_production_position": row.get("default_production_position") or "",
            })

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return Response(
            content=output.getvalue().encode("utf-8-sig"),  # BOM for Excel compat
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="products.csv"'},
        )
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Products"
        ws.append(EXPORT_COLUMNS)
        for row in rows:
            ws.append([row.get(c, "") for c in EXPORT_COLUMNS])
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        fname = "products_template.xlsx" if format == "template" else "products.xlsx"
        return Response(
            content=output.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{fname}"'},
        )


# =================================================
#  POST /import : IMPORT PRODUCTS (dry-run / execute)
# =================================================
#
# ROUTE ORDERING: this route MUST be declared before GET /{product_key} to prevent
# FastAPI from treating the literal segment "import" as a product key (Pitfall 1).
#
@router.post(
    "/import",
    response_model=None,
    responses={
        200: {"description": "Dry-run valid (file_key + counts) or execute result"},
        400: {"description": "Missing file/file_key, parse error, or missing required columns"},
        404: {"description": "Import file or metadata not found (execute path)"},
        422: {"description": "Validation errors in rows (dry-run returns xlsx) or unvalidated key"},
        500: {"description": "Database or file I/O error"},
    },
)
async def import_products(
    dry_run: bool = Form(True),
    file: Optional[UploadFile] = File(None),
    file_key: Optional[str] = Form(None),
    token=Depends(auth.verify_token),
):
    """
    Import products from a CSV/XLSX file using a two-call dry-run / execute flow.

    dry_run=True  (requires 'file' upload): validates references, returns either an
      annotated error xlsx (X-Error-Count header) or JSON {status, file_key, counts}.

    dry_run=False (requires 'file_key'): verifies the metadata sidecar, fires
      ProductImportedEvent.save(), returns APIResponse with created/skipped counts.

    Identity comes from the JWT token (token.consumer_key) — no user_key form field.

    **Emits:** ProductImportedEvent (execute path only)
    **Required scope:** product:catalogue:write
    """
    try:
        media_path = get_config().media_path
        import_dir = os.path.join(media_path, 'product_import')

        if dry_run:
            # ---- DRY-RUN: validate file in a read-only transaction ----

            if not file:
                raise HTTPException(status_code=400, detail="File is required for validation (dry_run=True)")

            file_content = await file.read()
            filename = file.filename or 'import.csv'

            # Parse (size/row caps enforced inside _parse_import_file — T-02-01)
            try:
                rows = _parse_import_file(file_content, filename)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            if not rows:
                raise HTTPException(status_code=400, detail="No data rows found in file")

            # Require 'code' column (only mandatory column)
            if 'code' not in rows[0]:
                raise HTTPException(status_code=400, detail="Missing required column: 'code'")

            # Detect extra columns that will be ignored
            ignored_columns = _detect_ignored_columns(rows, EXPORT_COLUMNS)

            # Read-only transaction: resolve refs + collect errors
            tx = db.begin_transaction(
                read=['Product', 'Tag', 'has_tag', 'PrintTemplate', 'can_use_print_template', 'Counter', 'Position']
            )
            error_rows: list[dict] = []
            valid_rows: list[dict] = []
            valid_codes: list[str] = []
            rows_out: list[dict] = []

            try:
                # Build ref lookups (same logic as the event, re-used in read-only tx)
                all_tag_names: set[str] = set()
                all_tmpl_names: set[str] = set()
                all_counter_names: set[str] = set()
                all_pos_codes: set[str] = set()

                for row in rows:
                    for n in (row.get('tags') or '').split(';'):
                        if n.strip():
                            all_tag_names.add(n.strip())
                    for n in (row.get('print_templates') or '').split(';'):
                        if n.strip():
                            all_tmpl_names.add(n.strip())
                    if c := (row.get('counter') or '').strip():
                        all_counter_names.add(c)
                    if p := (row.get('default_consumption_position') or '').strip():
                        all_pos_codes.add(p)
                    if p := (row.get('default_production_position') or '').strip():
                        all_pos_codes.add(p)

                def _bulk_lookup_ro(collection: str, field: str, values: set[str]) -> dict:
                    """T-02-03: bind vars only, never string-interpolated."""
                    if not values:
                        return {}
                    result = tx.aql.execute(
                        f'RETURN MERGE(FOR doc IN {collection} FILTER doc.{field} IN @vals'
                        f' RETURN {{ [doc.{field}]: doc._key }})',
                        bind_vars={'vals': list(values)}
                    ).next()
                    return result or {}

                tag_lk = _bulk_lookup_ro('Tag', 'name', all_tag_names)
                tmpl_lk = _bulk_lookup_ro('PrintTemplate', 'name', all_tmpl_names)
                ctr_lk = _bulk_lookup_ro('Counter', 'name', all_counter_names)
                pos_lk = _bulk_lookup_ro('Position', 'code', all_pos_codes)

                # enumerate(rows, start=2): row_number = xlsx row number
                # (header = row 1, first data = row 2) — matches _generate_error_file convention
                for row_number, row in enumerate(rows, start=2):
                    errs: list[str] = []
                    code = (row.get('code') or '').strip()
                    if not code:
                        errs.append("Missing required value: 'code'")

                    # Validate tag names
                    for name in (row.get('tags') or '').split(';'):
                        name = name.strip()
                        if name and name not in tag_lk:
                            errs.append(f"Unknown tag: '{name}'")

                    # Validate print_template names
                    for name in (row.get('print_templates') or '').split(';'):
                        name = name.strip()
                        if name and name not in tmpl_lk:
                            errs.append(f"Unknown print template: '{name}'")

                    # Validate counter name
                    ctr = (row.get('counter') or '').strip()
                    if ctr and ctr not in ctr_lk:
                        errs.append(f"Unknown counter: '{ctr}'")

                    # Validate consumption position
                    cpos = (row.get('default_consumption_position') or '').strip()
                    if cpos and cpos not in pos_lk:
                        errs.append(f"Unknown position code: '{cpos}' (consumption)")

                    # Validate production position
                    ppos = (row.get('default_production_position') or '').strip()
                    if ppos and ppos not in pos_lk:
                        errs.append(f"Unknown position code: '{ppos}' (production)")

                    # Type-mismatch: manage_inventory must be 'true' or 'false' (VAL-02)
                    if 'manage_inventory' in row:
                        raw_mi = (row.get('manage_inventory') or '').strip().lower()
                        if raw_mi and raw_mi not in ('true', 'false'):
                            errs.append(f"type-mismatch: 'manage_inventory' must be 'true' or 'false', got '{raw_mi}'")

                    if errs:
                        error_rows.append({'_row_number': row_number, '_errors': errs})
                        rows_out.append({'row': row_number, 'code': code or '', 'action': 'error', 'errors': errs})
                    else:
                        valid_rows.append(row)
                        if code:
                            valid_codes.append(code)
                        # Defer action assignment until after existing_codes bulk lookup
                        rows_out.append({'row': row_number, 'code': code, 'action': '__pending__', 'errors': []})

                # Approximate created/updated counts: bulk existing-code check
                created_count = 0
                updated_count = 0
                existing_codes: set[str] = set()
                if valid_codes:
                    existing_cursor = tx.aql.execute(
                        'FOR p IN Product FILTER p.code IN @codes AND !p.trash RETURN p.code',
                        bind_vars={'codes': valid_codes}
                    )
                    existing_codes = set(existing_cursor)
                    created_count = sum(1 for c in valid_codes if c not in existing_codes)
                    updated_count = len(valid_codes) - created_count

                # Assign create/update action to valid rows
                for entry in rows_out:
                    if entry['action'] == '__pending__':
                        entry['action'] = 'create' if entry['code'] not in existing_codes else 'update'

            finally:
                tx.abort_transaction()   # Read-only — ALWAYS abort, never commit

            # Error path: return annotated xlsx
            if error_rows:
                error_file_bytes = _generate_error_file(rows, error_rows, EXPORT_COLUMNS)
                return Response(
                    content=error_file_bytes,
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={
                        'Content-Disposition': 'attachment; filename="product_import_errors.xlsx"',
                        'X-Import-Status': 'error',
                        'X-Error-Count': str(len(error_rows)),
                        'X-Valid-Count': str(len(valid_rows)),
                    }
                )

            # Clean path: store file + metadata sidecar
            new_file_key = str(uuid.uuid4())
            os.makedirs(import_dir, exist_ok=True)

            file_path = os.path.join(import_dir, new_file_key)
            with open(file_path, 'wb') as f:
                f.write(file_content)

            metadata = {
                'user_key': token.consumer_key,
                'filename': filename,
                'validated': True,
            }
            meta_path = os.path.join(import_dir, f'{new_file_key}.meta.json')
            with open(meta_path, 'w') as mf:
                json.dump(metadata, mf)

            return {
                'status': 'valid',
                'file_key': new_file_key,
                'filename': filename,
                'rows_total': len(rows),
                'created_count': created_count,
                'updated_count': updated_count,
                'error_count': 0,
                'skipped_count': 0,
                'ignored_columns': ignored_columns,
                'rows': rows_out,
            }

        else:
            # ---- EXECUTE: fire the event from a validated file_key ----

            if not file_key:
                raise HTTPException(status_code=400, detail="file_key is required for import (dry_run=False)")

            # Verify sidecar exists and was validated (T-02-04)
            meta_path = os.path.join(import_dir, f'{file_key}.meta.json')
            file_path_check = os.path.join(import_dir, file_key)

            if not os.path.exists(file_path_check):
                raise HTTPException(status_code=404, detail="Import file not found. Please validate again.")
            if not os.path.exists(meta_path):
                raise HTTPException(status_code=404, detail="File metadata not found. Please validate again.")

            with open(meta_path, 'r') as mf:
                metadata = json.load(mf)

            if not metadata.get('validated'):
                raise HTTPException(status_code=422, detail="File was not validated. Please validate first.")

            event = ProductImportedEvent(
                info=EventInfoModel(
                    event_type=ProductImportedEvent.get_event_type(),
                    user_key=token.consumer_key,
                    import_file_key=file_key,
                    import_filename=metadata.get('filename', 'import.csv'),
                ).model_dump()
            )
            event.save()

            return APIResponse(
                message='Import complete',
                detail=event.response
            )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail=traceback.format_exc())


# =================================================
#  POST / : CREATE PRODUCT
# =================================================
@router.post("", status_code=201,
    response_model=APIResponse,
    responses={
      400: {"description": "Invalid form data or duplicate product code"},
      500: {"description": "Database write or image save error"},
    },
    dependencies=[Depends(auth.verify_token)])
async def create_product(
  code: str = Form(...),
  description: str = Form(''),
  image: UploadFile = File(None),
  traceability_level: str = Form(''),
  serial_code_on_creation: bool = False,
  counter_key: str = Form(''),
  manage_inventory: bool = Form(False)
):
  """Create a new product in the catalogue.

  Accepts multipart form data. Validates that no active product already exists
  with the same `code`. If an image is provided it is written to the product
  media folder as `image.jpg` inside a transaction.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:catalogue:create`
  """
  # Map form data
  try:

    new_product = ProductDetails(
      code=code,
      description=description,
      created=timestamp(),
      traceability_level='form_only' if len(traceability_level) else None,
      serial_code_on_creation=serial_code_on_creation,
      counter_key=counter_key,
      manage_inventory=manage_inventory
    )

  except Exception as e:
    error_str = traceback.format_exc()
    raise HTTPException(
      status_code=400,
      detail=f'The data provided cannot be read properly: \n{error_str}'
    )

  # Check if code is present
  if product_db.find(dict(code=code, trash=False)).count():
    status_code = 400
    response=dict(
      status=status_code,
      message="A product with the same code already exists"
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


  if image:
    new_product.image = True

  # Save data
  try:
    tx = db.begin_transaction(write=["Product"])
    prepped_data = jsonable_encoder(new_product, by_alias=True, exclude_none=True )
    db_response = tx.collection("Product").insert(prepped_data, return_new=True)

    # Save image
    if image:
      product_image = FileHandler.product_media(
        object_key=db_response['_key'],
        file=image,
      )

      try:
        await product_image.write_file(custom_name='image.jpg')

      except:
        tx.abort_transaction()
        raise HTTPException(
          status_code=500,
          detail="There was an error saving the image"
        )

    tx.commit_transaction()

    # Close request and return response
    status_code = 200
    message = "Product created"
    response = APIResponse(
      status_code=status_code,
      message=message,
      # Arango replies by sending a json that includes id, key, rev and
      # then again the whole document nested in the main objecy,
      # thus duplicating the above keys. Below we get only the whole document.
      detail=db_response['new']
    )
    return response

  except Exception:
    tx.abort_transaction()
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


# =================================================
#  POST /PRODUCT_KEY/COPY : COPY PRODUCT
# =================================================
@router.post("/copy", status_code=201,
    response_model=APIResponse,
    responses={
      404: {"description": "Original product not found"},
      409: {"description": "A product with the new code already exists"},
      500: {"description": "Database or file-copy error"},
    },
    dependencies=[Depends(auth.verify_token)])
async def copy_product(
  original_product: str = Body(), # Can be product key or code (key default)
  new_code: str = Body(),
  new_description: str = Body(None),
  by_code: bool = Body(default=False)
  ):
  """Create a new product as a deep copy of an existing one.

  Duplicates the product record, its full production process (phases + steps),
  media folder, print-template assignments, and tag connections under `new_code`.
  Pass `by_code=true` to look up the original product by `code` instead of
  `_key`. Returns HTTP 409 if a product with `new_code` already exists.

  All mutations run inside a single ArangoDB transaction.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:catalogue:create`
  """

  # 0.1 Check no product exists with same code
  if db.collection('Product').find(dict(code=new_code, trash=False)).count():
    raise HTTPException(
      status_code=409,
      detail="A product with the same code already exists"
    )

  # 0.2 Setup transaction
  tx = db.begin_transaction(write={'Product', 'can_use_print_template', 'has_tag', *copy_process_to_product_writes}, read=['Operation'])
  product_db = tx.collection('Product')

  # 0.3 Fetch product data
  try:
    if by_code:
      match = dict(code=original_product, trash=False)

    else: # Copy product by key
      match = dict(_key=original_product, trash=False)

    new_product = ProductDetails(**product_db.find(match).next())
    new_product.created = timestamp()

    original_product_code = new_product.code
    original_product_description = new_product.description
    original_product_key = new_product.key

  except StopIteration:
    tx.abort_transaction()
    raise HTTPException(
      status_code=404,
      detail="No product with the provided code or key could be found"
    )

  except Exception:
    tx.abort_transaction()
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  def copy_print_templates(collection_name, from_key, to_key):
    print_template_cursor = tx.collection('can_use_print_template').find(dict(_from=f'{collection_name}/{from_key}'))
    if print_template_cursor.count() > 0:
      new_print_templates = []
      for edge in print_template_cursor:
        new_print_templates.append(dict(_from=f'{collection_name}/{to_key}', _to=edge['_to']))

      tx.collection('can_use_print_template').insert_many(new_print_templates, silent=True)

  try:
    # 1. CREATE NEW PRODUCT WITH PROVIDED CODE
    new_product.code = new_code
    new_product.description = new_description or original_product_description
    new_product.active = True
    new_product.key = None

    prepped_data = jsonable_encoder(new_product, by_alias=True, exclude_none=True)
    new_product_key = product_db.insert(prepped_data)['_key']

    # 2 COPY PROCESS
    # See also update_process endpoint in endpoints/process.py

    bind_vars = dict(product_key=original_product_key)
    process_cursor = tx.aql.execute(ProcessQueries.GET_PRODUCTION_PROCESS, bind_vars=bind_vars)
    process = [PhaseData(**phase) for phase in process_cursor]

    product_db.update(dict(
      _key=new_product_key,
      process_phases=copy_process_to_product(tx, process, new_product_key)
    ))

    # 7. Copy product media folder (if present) with new product key
    product_media = FileHandler.product_media(original_product_key)
    if os.path.isdir(product_media.folder_path):
      product_media.copy_media(new_product_key)

    #TODO
    """
    Delete media folders created if something goes wrong
    """

    # 8. Copy product print templates
    copy_print_templates('Product', original_product_key, new_product_key)

    # 9. Copy tags
    tag_ids_cursor = tx.aql.execute(
      """
      FOR edge IN has_tag
        FILTER edge._from == @from_id
        RETURN edge._to
      """,
      bind_vars=dict(
        from_id=f'Product/{original_product_key}',
      )
    )
    tag_connections = [
      dict(
        _from=f'Product/{new_product_key}',
        _to=tag_id,
      ) for tag_id in tag_ids_cursor
    ]
    if tag_connections:
      tx.collection('has_tag').insert_many(tag_connections)

    # 10. Commit transaction
    tx.commit_transaction()

    return APIResponse(
      status_code=201,
      message=f"Created product {new_code} as copy of product {original_product_code}.",
      detail=dict(new_product_key=new_product_key)
    )

  except:
    tx.abort_transaction()
    status_code = 500
    error_str = traceback.format_exc()
    response=dict(
      status=status_code,
      message="There was a problem saving the data into the database. Please contact support if it happens again",
      error=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )




# =================================================
#  DELETE /PRODUCT_KEY : DELETE PRODUCT
# =================================================
@router.delete("/{product_key}",
    response_model=APIResponse,
    responses={500: {"description": "Database update error"}},
    dependencies=[Depends(auth.verify_token)])
async def delete_product(product_key):
  """Soft-delete a product by moving it to the trash.

  Sets `trash=true` on the product document rather than removing it, preserving
  historical production data. The product will no longer appear in active
  product lists.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:catalogue:delete`
  """
  product_to_trash = product_db.get(product_key)

  # TODO: Verify if there's any workorder or active item related
  # How to deal with historical data?

  try:
    updated_product = product_db.update(dict(_key=product_key, trash=True), return_new=True)['new']
    response = APIResponse(
      status_code=200,
      message=f"Product {updated_product['code']} (KEY: {product_key}) moved to trash",
      detail=updated_product
    )
    return response

  except:
    status_code=500
    response=dict(
      status=status_code,
      message="Couldn't delete product on the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

# =================================================
#  PATCH /PRODUCT_KEY : UPDATE PRODUCT (SPECIFC PROPERTIES)
# =================================================
@router.patch("/{product_key}",
    response_model=APIResponse,
    responses={500: {"description": "Database update error"}},
    dependencies=[Depends(auth.verify_token)])
async def udpate_product(
  product_key: str | None = None,
  updated_fields: dict = dict()
):
  """Partially update specific fields of a product document.

  Merges `updated_fields` into the product document, stamping the `updated`
  timestamp. Only the supplied keys are changed; other fields are unaffected.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:catalogue:update`
  """

  product_to_update = product_db.get(product_key)
  try:
    updated_product = product_db.update(
      dict(
        _key=product_key,
        updated=timestamp(),
        **updated_fields
      ), return_new=True
    )['new']
    response = APIResponse(
      status=200,
      message=f"Product {updated_product['code']} (KEY: {updated_product['_key']}) updated",
      detail=updated_product
    )
    return response

  except:
    status_code = 500
    response=dict(
      status=status_code,
      message="Couldn't update product on the db",
      error=traceback.format_exc()
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )


# =================================================
#  PUT /PRODUCT_KEY : REPLACE PRODUCT
# =================================================
@router.put("/{product_key}",
    response_model=dict,
    responses={500: {"description": "Database replace error"}},
    dependencies=[Depends(auth.verify_token)])
async def replace_product(
  product_key: str,
  new_product_data: ProductDetails,
):
  """Fully replace a product document.

  Performs a full document replace (not a merge) — all fields in the document
  will reflect `new_product_data`. The `_key` in the payload must match
  `product_key`.

  **Emits:** *(direct transaction — no event class)*

  **Required scope:** `product:catalogue:update`
  """

  # new_product_data.key = product_key
  # can comment the above out, since the key is already included in the data
  prepped_data = jsonable_encoder(new_product_data, by_alias=True)
  saved_product = product_db.replace(prepped_data, return_new=True)['new']

  return saved_product


# =================================================
#  POST /PRODUCT_KEY/DOCS : SAVE DOC
# =================================================
@router.post("/{product_key}/doc",
    response_model=str,
    responses={400: {"description": "File write error"}},
    dependencies=[Depends(auth.verify_token)])
async def save_doc(
  product_key: str,
  new_doc: UploadFile =  File(...)
):
  """Upload a document file and attach it to a product.

  Saves the uploaded file to the product's `doc` subfolder. Returns the stored
  filename on success.

  **Emits:** *(direct file write — no event class)*

  **Required scope:** `product:catalogue:update`
  """

  doc = FileHandler.product_media(
    object_key=product_key,
    subfolder="doc",
    file=new_doc,
    name=new_doc.filename
  )
  try:
    await doc.write_file()
  except:
    error_str = traceback.format_exc()
    status_code = 400
    response=dict(
      status=status_code,
      message="There was an error writing the file to disk",
      error_str=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )

  return doc.name

# =================================================
#  DELETE (DOCS)
# =================================================
@router.delete("/{product_key}/doc/{doc_name}",
    response_model=None,
    responses={500: {"description": "File deletion error"}},
    dependencies=[Depends(auth.verify_token)])
async def delete_doc(
  product_key: str,
  doc_name: str
):
  """Delete a document file from a product's doc folder.

  Removes the file `doc_name` from the product's document storage.
  Returns no body on success.

  **Emits:** *(direct file delete — no event class)*

  **Required scope:** `product:catalogue:update`
  """

  doc = FileHandler.product_media(
    object_key=product_key,
    subfolder='doc',
    name=doc_name
  )

  doc.delete_file()


# =================================================
#  PUT (IMAGE)
# =================================================
@router.put("/{product_key}/image",
    response_model=APIResponse,
    responses={500: {"description": "Image write or database update error"}},
    dependencies=[Depends(auth.verify_token)])
async def replace_product_image(
  product_key: str,
  new_image: UploadFile = File(...)
):
  """Replace the product's primary image.

  Writes the uploaded file to the product media folder as `image.jpg` and sets
  `image=true` in the product document. Any previous image file is overwritten.

  **Emits:** *(direct file write — no event class)*

  **Required scope:** `product:catalogue:update`
  """
  # extension = new_image.filename.split('.')[-1]
  img = FileHandler.product_media(object_key=product_key, file=new_image)
  filename = 'image.jpg'
  product_db.update(dict(
    _key=product_key,
    updated=timestamp(),
    image=True
  ))
  await img.write_file(custom_name=filename)
  return APIResponse(message="File saved correctly")



# =================================================
#  DELETE (IMAGE)
# =================================================
@router.delete("/{product_key}/image",
    response_model=None,
    responses={500: {"description": "Image deletion or database update error"}},
    dependencies=[Depends(auth.verify_token)])
async def replace_product_image(product_key: str):
  """Delete the product's primary image.

  Removes `image.jpg` from the product media folder and sets `image=false` in
  the product document. Returns no body on success.

  **Emits:** *(direct file delete — no event class)*

  **Required scope:** `product:catalogue:update`
  """
  # extension = new_image.filename.split('.')[-1]
  img = FileHandler.product_media(object_key=product_key)
  img.delete_file('image.jpg')
  product_db.update(dict(
    _key=product_key,
    updated=timestamp(),
    image=False
  ))


# =================================================
#  GET /PRODUCT_KEY : GET PRODUCT DATA
# =================================================
@router.get("/{product_key}", response_model=ProductFull,
    responses={
      404: {"description": "Product not found"},
      500: {"description": "Database fetch or validation error"},
    },
    dependencies=[Depends(auth.verify_token)])
async def get_product_data(product_key: str):
  """Retrieve full product details including docs and counter.

  Returns a `ProductFull` object for `product_key`, enriched with:
  - `docs`: list of document files in the product doc folder.
  - `counter`: the associated `Counter` document if `counter_key` is set.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `product:catalogue:read`
  """
  try:
    product = ProductFull(**product_db.get(product_key))
    product.docs = get_product_docs(product_key)
    if (product.counter_key):
      product.counter = db.collection('Counter').get(product.counter_key)
    return product

  except:
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="There was an error getting data from the database.",
      error_str=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )



# =================================================
#  PRODUCT STATS
# =================================================
@router.get('/{product_key}/stats',
    response_model=dict,
    responses={500: {"description": "KPI query error"}},
    dependencies=[Depends(auth.verify_token)])
async def get_product_stats(product_key: str):
  """Retrieve KPI statistics for a product.

  Runs the `GET_PRODUCT_STATS` query and returns aggregated metrics such as
  throughput time, yield rate, and production counts within the product's
  configured KPI window.

  **Emits:** *(direct query — no event class)*

  **Required scope:** `product:catalogue:read`
  """
  try:
    stats = db.aql.execute(ProductStatQueries.GET_PRODUCT_STATS, bind_vars=dict(product_key=product_key)).next()
    return stats

  except:
    error_str = traceback.format_exc()
    status_code = 500
    response=dict(
      status=status_code,
      message="There was an error getting data from the database.",
      error_str=error_str
    )
    raise HTTPException(
      status_code=status_code,
      detail=response
    )
