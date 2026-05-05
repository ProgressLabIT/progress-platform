import io
import json
import re
import traceback
from typing import Annotated, List, Union

from base64 import b64decode
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from pypdf import PdfReader, PdfWriter
from pydantic import AfterValidator

from models.serial import SerialSelection, Serial, SerialTreeNode
from utils import auth
from utils.db import db
from utils.serial import Queries, get_serial_child_nodes
from utils.search import wildcard_to_regex
from utils.dhr import generate_dhr_for_serial

router = APIRouter()


def sanitize_filename(filename):
  """
  Sanitize filename for use in HTTP headers by removing or replacing invalid characters
  """
  # Remove or replace characters that are not allowed in HTTP headers
  # Keep only alphanumeric, spaces, hyphens, underscores, and dots
  sanitized = re.sub(r'[^\w\s\-_.]', '_', filename)
  # Replace multiple consecutive spaces/underscores with single underscore
  sanitized = re.sub(r'[\s_]+', '_', sanitized)
  # Remove leading/trailing underscores
  sanitized = sanitized.strip('_')
  return sanitized


@router.get('/serial-field',
    response_model=list,
    responses={},
    dependencies=[Depends(auth.verify_token)])
def fetch_field():
  """Return the configured serial custom field definitions.

  Reads the `serial_fields` key from the `Config` collection and returns the
  list of field definitions used to render extra data entry forms for serial
  numbers. Returns an empty list if no serial fields have been configured.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  return fields

@router.get('/serial-batch',
    response_model=list,
    responses={},
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(
  batch_key: str | None = None,
  filter_empty: bool = False
):
  """Return all serials belonging to a production batch.

  Queries the `GET_ALL_SERIALS_IN_BATCH` AQL query against the `Serial`
  collection for the given `batch_key`. When `filter_empty=True`, serials
  without a code are excluded from the result.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  bind_vars = dict(batch_key = batch_key)
  batch_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_ALL_SERIALS_IN_BATCH, bind_vars=bind_vars)]:
    if serial['code'] or not filter_empty:
      batch_serials.append(serial)
  return batch_serials

@router.get('/component-batch',
    response_model=list,
    responses={},
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(batch_key: str | None = None):
  """Return all component serials linked to a batch.

  Queries the `GET_ALL_COMPONENTS_IN_BATCH` AQL query starting from
  `Batch/<batch_key>` and returns all serials that are linked as components
  via the `contains` edge collection.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  bind_vars = dict(
    from_id = f'Batch/{batch_key}'
  )
  return [e for e in db.aql.execute(Queries.GET_ALL_COMPONENTS_IN_BATCH, bind_vars=bind_vars)]

@router.get('/serial-parents',
    response_model=list,
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
def get_serial_parents(
  serial_key: str | None = None,
):
  """Return the ancestor chain for a serial number.

  Traverses the `contains` edge collection upward from `Serial/<serial_key>`
  and returns the list of parent serials in bottom-up order (closest parent
  first), then reverses it so the root ancestor is first.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  try:
    bind_vars = dict(
      serial_id = f'Serial/{serial_key}'
    )
    cursor = db.aql.execute(Queries.GET_SERIAL_PARENTS, bind_vars=bind_vars)
    parents = [i for i in cursor]
    return parents[::-1]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-children',
    response_model=list,
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
def get_serial_children(
  serial_key: str | None = None,
):
  """Return the direct children of a serial number.

  Traverses one level down the `contains` edge collection from
  `Serial/<serial_key>` and returns all immediate child serials.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  try:
    bind_vars = dict(
      serial_id = f'Serial/{serial_key}',
      level = 1
    )
    cursor = db.aql.execute(Queries.GET_SERIAL_CHILDREN, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-hierarchy',
    response_model=list[SerialTreeNode],
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
def get_serial_hierarchy(
  serial_key: str,
  include_expected_components: bool = True,
):
  """Get the serial hierarchy, from the root ancestor (the one with no parent) to all descendants of the given serial.

  Resolves the root ancestor of `serial_key` using `GET_SERIAL_ROOT_ANCESTOR`,
  then builds a full recursive `SerialTreeNode` tree by walking the `contains`
  edge collection downward. Returns a list containing the single root node with
  all descendants nested under `children`.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  try:
    # Get the root ancestor of the serial
    bind_vars = dict(serial_id = f'Serial/{serial_key}')
    root_node = SerialTreeNode(**db.aql.execute(Queries.GET_SERIAL_ROOT_ANCESTOR, bind_vars=bind_vars).next())
    if root_node.serial_key is None: # no ancestor found, so we're at the root
      serial = db.collection('Serial').get(serial_key)
      product = db.collection('Product').get(serial['product_key'])
      root_node = SerialTreeNode(
        serial_key = serial_key,
        product_key = product['_key'],
        serial_code = serial['code'],
        product_code = product['code'],
        product_description = product['description'],
      )

    serial_children = list(db.aql.execute(
      Queries.GET_SERIAL_CHILDREN,
      bind_vars=dict(serial_id = f'Serial/{root_node.serial_key}')
    ))

    # build_serial_tree is a recursive function that returns the next tree level
    root_node.children = get_serial_child_nodes(root_node, serial_children)
    return [root_node]

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials hierarcy from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/wip-serial',
    response_model=list[SerialSelection],
    responses={},
    dependencies=[Depends(auth.verify_token)])
def get_serial_wip(
  wo_key: str | None = None,
  job_key: str | None = None,
  phase_key: str | None = None,
):
  """Return WIP serials available for a work order, job, or phase.

  Queries `GET_AVAILABLE_WIP_SERIALS` to find serials currently in WIP status
  that can be assigned to the given work order, job, or phase combination.
  Used by the production UI to populate the serial selector when starting a batch.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  bind_vars = dict(
    wo_key = wo_key,
    phase_key = phase_key,
    job_key = job_key
  )
  cursor = db.aql.execute(Queries.GET_AVAILABLE_WIP_SERIALS, bind_vars=bind_vars)
  return [SerialSelection(**s) for s in cursor]

@router.get('/serial-selection',
    response_model=list,
    responses={},
    dependencies=[Depends(auth.verify_token)])
def get_serial_selection(
  search: str | None = None,
  wo_key: str | None = None,
  product_key: str | None = None,
  batch_key: str | None = None,
  free_only: bool = False,
  inventory_only: bool = False,
  inventory_in_position_key: str | None = None,
  include_unreleased: bool = False,
  limit: int = 100
):
  """Return a filtered list of serials for use in UI selection widgets.

  Executes `GET_ALL_SERIALS` with the given filters and returns serial objects
  suitable for display in dropdowns and search-as-you-type widgets. Supports
  filtering by work order, product, batch, inventory state, and release status.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  return [e for e in db.aql.execute(Queries.GET_ALL_SERIALS, bind_vars=dict(
    search = search,
    wo_key = wo_key,
    product_key = product_key,
    batch_key = batch_key,
    limit = limit,
    free_only = free_only,
    inventory_only = inventory_only,
    inventory_in_position_key = inventory_in_position_key,
    include_unreleased = include_unreleased
  ))]


# ---------------------------------------------
# SERIALS
# ---------------------------------------------

@router.get('/serial/{serial_key}',
    response_model=dict,
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_key(serial_key: str):
  """Fetch a serial document by its primary key.

  Retrieves the raw `Serial` document from ArangoDB by `serial_key`. Returns
  the full document including all custom data fields and lifecycle timestamps.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  try:
    return db.collection('Serial').get(serial_key)
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-code',
    response_model=list,
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_code(serial_code: str | None = None,
                         product_key: str | None = None):
  """Look up serials by code and optional product filter.

  Executes `GET_SERIALS_FOR_CODE` to find all `Serial` documents whose `code`
  matches `serial_code`, optionally scoped to a specific product. Serial codes
  are normalized to uppercase before the query.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  bind_vars = dict(
    serial_code = serial_code,
    product_key = product_key
  )
  try:
    cursor = db.aql.execute(Queries.GET_SERIALS_FOR_CODE, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )

@router.get('/serial-code/verify-free',
    response_model=bool,
    responses={},
    dependencies=[Depends(auth.verify_token)])
def verify_serial_code_free(serial_code: str | None = None,
                         product_key: str | None = None,
                         serial_key: str | None = None):
  """Check whether a serial code is available for use.

  Executes `GET_SERIALS_FOR_SERIAL_CODE` and returns `True` if no other
  `Serial` document already uses the given `serial_code` for the given product
  (excluding `serial_key` itself, used for edit scenarios).

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  cursor = db.aql.execute(
     Queries.GET_SERIALS_FOR_SERIAL_CODE,
          bind_vars=dict(
            serial_key=serial_key,
            serial=serial_code,
            product_key=product_key
          )
        )
  try:
    return len([Serial(**t) for t in cursor])<=0
  except:
     return False

@router.get('/serial',
    response_model=list,
    responses={500: {"description": "Database error"}},
    dependencies=[Depends(auth.verify_token)])
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  serial_search: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  is_contained_in: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  contains: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  created_by: Union[List[str], None] = Query(default=None),
  advanced_filters: str = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  work_order_search: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  project_search: Annotated[str | None, AfterValidator(wildcard_to_regex)] = None,
  limit: int | None = 200,
  include_deleted: bool = False,
  offset: int | None = None,
  filter_unreleased: bool = False,
  time_released_from: datetime | None = None,
  time_released_to: datetime | None = None,
  sort_by: str | None = 'created',
  sorting_order: str | None = 'desc',
  ):
  """Search serials with rich filtering and sorting.

  Executes the `FIND_SERIALS` AQL query with the full set of filter parameters.
  Wildcard search fields (`serial_search`, `product_code_search`, etc.) accept
  shell-style wildcards (`*`, `?`) which are converted to AQL regex before
  execution. `advanced_filters` accepts a base64-encoded JSON array of custom
  field filters.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """

  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  # use query parameters to filter specific type
  bind_vars = dict(
    serial_key = serial_key,
    serial_search = serial_search,
    time_created_from = time_created_from,
    time_created_to = time_created_to,
    created_by = created_by,
    product_key = product_key,
    product_code_search = product_code_search,
    is_contained_in = is_contained_in,
    contains = contains,
    work_order_search = work_order_search,
    project_search = project_search,
    filter_unreleased = filter_unreleased,
    advanced_filters = json.loads(b64decode(advanced_filters).decode('latin-1')) if advanced_filters else None,
    limit = limit,
    offset = offset,
    include_deleted = include_deleted,
    fields = fields,
    sort_by = sort_by,
    sorting_order = sorting_order,
    time_released_from = time_released_from,
    time_released_to = time_released_to
  )
  try:
    cursor = db.aql.execute(Queries.FIND_SERIALS, bind_vars=bind_vars)
    return [i for i in cursor]
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error fetching serials from the db.",
        error=traceback.format_exc()
      )
    )




@router.get('/serial/{serial_key}/dhr',
    response_model=None,
    responses={
      404: {"description": "Serial not found"},
      500: {"description": "PDF generation error"},
    },
    dependencies=[Depends(auth.verify_token)])
def get_device_history_record(serial_key: str, include_attachments: bool = False, include_children: bool = False, include_step_data: bool = False):
  """Generate a device history record for a serial.

  Renders a PDF Device History Record (DHR) for the serial identified by
  `serial_key` using WeasyPrint. When `include_children=True`, DHRs for all
  complex child serials (those with step data or sub-children) are appended in
  order of product code then serial code. Returns the combined PDF as a binary
  download attachment.

  **Emits:** *(direct query — no event class)*
  **Required scope:** `serial:read`
  """
  try:
    # Fetch children serials using GET_SERIAL_CHILDREN_FOR_DHR query for DHR generation
    children_serials = []
    if include_children:
      try:
        bind_vars = dict(serial_id=f'Serial/{serial_key}')
        children_result = list(db.aql.execute(Queries.GET_SERIAL_CHILDREN_FOR_DHR, bind_vars=bind_vars))
        children_serials = children_result
      except Exception:
        # If children fetching fails, continue without children data
        children_serials = []

    # Generate main DHR using WeasyPrint
    main_pdf_bytes = generate_dhr_for_serial(serial_key, include_attachments, include_step_data)
    if not main_pdf_bytes:
      raise HTTPException(status_code=404, detail=dict(message=f"Serial {serial_key} not found"))

    # Prepare PDF writer and append the main DHR
    writer = PdfWriter()
    main_reader = PdfReader(io.BytesIO(main_pdf_bytes))
    for pg in main_reader.pages:
      writer.add_page(pg)

    # Generate and append DHRs only for complex children (those with data or children) if include_children is True
    if include_children and children_serials:
      # Filter to only complex children (those with data or sub-children)
      complex_children = [child for child in children_serials if child.get('has_data') or child.get('has_children')]

      # Sort children by product code first, then serial code
      complex_children.sort(key=lambda x: (x.get('product_code') or '', x.get('serial_code') or ''))

      for child in complex_children:
        child_serial_key = child.get('serial_key')
        if child_serial_key:
          try:
            # Pass through include_attachments to children DHRs so they can have their own attachments
            child_pdf_bytes = generate_dhr_for_serial(child_serial_key, include_attachments, include_step_data)
            if child_pdf_bytes:
              child_reader = PdfReader(io.BytesIO(child_pdf_bytes))
              for pg in child_reader.pages:
                writer.add_page(pg)
          except Exception:
            # Continue if child DHR generation fails
            continue

    # Serialize combined PDF
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    # Generate filename from the main serial
    main_serial_data = db.collection('Serial').get(serial_key)
    serial_code = main_serial_data['code'] if main_serial_data else None

    raw_filename = f"DHR_{serial_code or serial_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filename = sanitize_filename(raw_filename)

    return Response(
        content=output.getvalue(),
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error generating the device history record.",
        error=traceback.format_exc()
      )
    )
