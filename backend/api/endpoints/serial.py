import traceback
import json

from base64 import b64decode
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
import io
from utils import auth
from datetime import datetime
from typing import List, Union

from models.serial import SerialSelection, Serial, SerialTreeNode
from utils.db import db
from utils.serial import Queries, get_serial_child_nodes, generate_dhr_for_serial
from pypdf import PdfReader, PdfWriter

router = APIRouter()

# DHR generation has been moved to utils/serial.py

@router.get('/serial-field',
    dependencies=[Depends(auth.verify_token)])
def fetch_field():
  serial_fields = db.collection('Config').get('serial_fields')
  fields = []
  if serial_fields is not None:
    fields = serial_fields['value']
  return fields

@router.get('/serial-batch',
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(
  batch_key: str | None = None,
  filter_empty: bool = False
):
  bind_vars = dict(batch_key = batch_key)
  batch_serials = []
  for serial in [e for e in db.aql.execute(Queries.GET_ALL_SERIALS_IN_BATCH, bind_vars=bind_vars)]:
    if serial['code'] or not filter_empty:
      batch_serials.append(serial)
  return batch_serials

@router.get('/component-batch',
    dependencies=[Depends(auth.verify_token)])
def get_serial_batch(batch_key: str | None = None):
  bind_vars = dict(
    from_id = f'Batch/{batch_key}'
  )
  return [e for e in db.aql.execute(Queries.GET_ALL_COMPONENTS_IN_BATCH, bind_vars=bind_vars)]

@router.get('/serial-parents',
    dependencies=[Depends(auth.verify_token)])
def get_serial_parents(
  serial_key: str | None = None,
):
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
    dependencies=[Depends(auth.verify_token)])
def get_serial_children(
  serial_key: str | None = None,
):
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

@router.get('/serial-hierarchy', dependencies=[Depends(auth.verify_token)])
def get_serial_hierarchy(
  serial_key: str,
  include_expected_components: bool = True,
):
  """
  Get the serial hierarchy, from the root ancestor (the one with no parent) to all descendants of the given serial.
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
    dependencies=[Depends(auth.verify_token)])
def get_serial_wip(
  wo_key: str | None = None,
  job_key: str | None = None,
  phase_key: str | None = None,
):
  bind_vars = dict(
    wo_key = wo_key,
    phase_key = phase_key,
    job_key = job_key
  )
  cursor = db.aql.execute(Queries.GET_AVAILABLE_WIP_SERIALS, bind_vars=bind_vars)
  return [SerialSelection(**s) for s in cursor]

@router.get('/serial-selection',
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
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_key(serial_key: str):
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
    dependencies=[Depends(auth.verify_token)])
def get_serial_from_code(serial_code: str | None = None,
                         product_key: str | None = None):
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
    dependencies=[Depends(auth.verify_token)])
def verify_serial_code_free(serial_code: str | None = None,
                         product_key: str | None = None,
                         serial_key: str | None = None):
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
    dependencies=[Depends(auth.verify_token)])
async def search_serials(
  serial_key: Union[List[str], None] = Query(default=None),
  serial_search: str | None = None,
  is_contained_in: str | None = None,
  contains: str | None = None,
  time_created_from: datetime | None = None,
  time_created_to: datetime | None = None,
  created_by: Union[List[str], None] = Query(default=None),
  advanced_filters: str = Query(default=None),
  product_key: Union[List[str], None] = Query(default=None),
  product_code_search: str | None = None,
  work_order_search: str | None = None,
  project_search: str | None = None,
  limit: int | None = 200,
  include_deleted: bool = False,
  offset: int | None = None,
  filter_unreleased: bool = False,
  time_released_from: datetime | None = None,
  time_released_to: datetime | None = None,
  sort_by: str | None = 'created',
  sorting_order: str | None = 'desc',
  ):

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




@router.get('/serial/{serial_key}/dhr', dependencies=[Depends(auth.verify_token)])
def get_device_history_record(serial_key: str, include_attachments: bool = False, include_children: bool = False, include_step_data: bool = False):
  """Generate a device history record for a serial"""
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
    main_serial_data = list(db.aql.execute("""
      LET s = DOCUMENT(Serial, @serial_key)
      RETURN s ? s.code : null
    """, bind_vars=dict(serial_key=serial_key)))
    serial_code = main_serial_data[0] if main_serial_data else None

    filename = f"DHR_{serial_code or serial_key}.pdf"
    return StreamingResponse(output, media_type='application/pdf', headers={
      'Content-Disposition': f'inline; filename="{filename}"'
    })

  except HTTPException:
    raise
  except Exception:
    raise HTTPException(
      status_code=500,
      detail=dict(
        message="There was an error generating the device history record.",
        error=traceback.format_exc()
      )
    )
