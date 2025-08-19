import traceback
import json
import os
import base64
import io
from typing import Dict, Any, List, Tuple

from models.bom import BomLineRead
from models.serial import SerialTreeNode
from utils.bom import get_bom_from_db
from utils.db import db
from utils.config import get_config
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

class Queries:

  GET_BATCH_SERIALS = """
    FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
    SORT s.code, s._key
    RETURN s
  """

  GET_ALL_SERIALS_IN_BATCH = """
    FOR edge IN batch_serial
      FILTER edge._from == CONCAT('Batch/', @batch_key)
      LET serial = DOCUMENT(Serial, edge._to)

      LET children = (
          FOR linked_serial IN contains
              FILTER linked_serial.wo_key == serial.wo_key
              && linked_serial._from == serial._id
              && linked_serial.replaced == false
              RETURN DOCUMENT(Serial, linked_serial._to)
          )
      SORT serial.code, serial._key
      RETURN MERGE(serial, { children })
  """

  GET_ALL_COMPONENTS_IN_BATCH = """
    FOR linked_serial IN contains
      FILTER linked_serial._from == @from_id
      RETURN DOCUMENT(Serial, linked_serial._to)
  """


  GET_SERIAL_PARENTS = """
      LET start = @serial_id
        FOR v, e IN 0..9999 INBOUND start contains OPTIONS { uniqueVertices: "path" }
          LET product = DOCUMENT(Product, v.product_key)
          RETURN merge({
              serial_key: v._key,
              replaced: e.replaced,
              serial_code: v.code,
              product_key: product._key,
              product_code: product.code,
              product_description: product.description
      })

  """

  GET_SERIAL_HIERARCHY = """
      LET start = @serial_id
        FOR v, e IN 0..9999 ANY start contains OPTIONS { uniqueVertices: "path" }
          LET product = DOCUMENT(Product, v.product_key)
          FILTER v.deleted == false

          RETURN {
              serial_id: v._id,
              serial_key: v._key,
              replaced: e.replaced,
              serial_code: v.code,
              product_key: product._key,
              product_code: product.code,
              product_description: product.description,
              from: e._from,
              to: e._to
          }
  """


  GET_SERIAL_ROOT_ANCESTOR = """
    // The root ancestor is the last vertex of the longest path in the inbound contains chain
    LET ancestors = (
      FOR v, e, p IN 0..999 INBOUND @serial_id contains
      FILTER
        v.deleted == false
        && e.replaced == false
      SORT length(p.vertices) DESC
      RETURN p.vertices[-1]
    )
    LET root = ancestors[0]
    LET product = DOCUMENT(Product, root.product_key)
    RETURN  {
      serial_key: root._key,
      product_key: root.product_key,
      serial_code: root.code,
      product_code: product.code,
      product_description: product.description
    }
  """

  GET_SERIAL_CHILDREN = """
    LET start = @serial_id
    FOR v, e IN 1..999 OUTBOUND start contains
    PRUNE e.replaced == true || e.confirmed == false
    LET product = DOCUMENT(Product, v.product_key)
    RETURN {
      parent_key: PARSE_IDENTIFIER(e._from).key,
      serial_key: v._key,
      replaced: e.replaced,
      serial_code: v.code,
      product_key: product._key,
      product_code: product.code,
      product_description: product.description,
      confirmed: NOT_NULL(e.confirmed, true)
    }
  """

  GET_SERIAL_CHILDREN_FOR_DHR = """
    LET start = @serial_id
    FOR v, e IN 1..999 OUTBOUND start contains
    PRUNE e.replaced == true || e.confirmed == false
    LET product = DOCUMENT(Product, v.product_key)
    LET has_data = LENGTH(NOT_NULL(v.data, [])) > 0
    LET has_children = COUNT(
      FOR child_v, child_e IN 1..1 OUTBOUND v._id contains
      FILTER child_e.replaced == false && NOT_NULL(child_e.confirmed, true) == true
      RETURN 1
    ) > 0
    RETURN {
      parent_key: PARSE_IDENTIFIER(e._from).key,
      serial_key: v._key,
      replaced: e.replaced,
      serial_code: v.code,
      product_key: product._key,
      product_code: product.code,
      product_description: product.description,
      confirmed: NOT_NULL(e.confirmed, true),
      has_data: has_data,
      has_children: has_children
    }
  """


  GET_ALL_SERIALS = """
    LET batch_serials = @batch_key ? (
      FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
      RETURN s._key
    ) : null
    FOR s IN Serial
    FILTER
      (@wo_key? s.wo_key == @wo_key: true)
      && (@product_key? s.product_key == @product_key: true)
      && (@search ? CONTAINS(LOWER(s.code), LOWER(@search)) : true)
      && (@include_unreleased ? true : s.released != null)
      && (@batch_key ? s._key IN batch_serials : true)
      && s.deleted == false

    LET used = COUNT(
      FOR linked_serial IN contains
      FILTER linked_serial._to == s._id
      && linked_serial.replaced == false
      RETURN 1
    ) > 0

    LET available = used ? false : COUNT(
      FOR inventory IN is_in_position
      FILTER inventory.serial_key == s._key
      FILTER @inventory_in_position_key ? PARSE_IDENTIFIER(inventory._to).key == @inventory_in_position_key : true
      RETURN 1
    ) > 0

    FILTER @free_only ? !used : true
    FILTER @inventory_only ? available : true

    SORT s.code
    LIMIT @limit
    RETURN merge(s, { used, available })
  """

  GET_SERIALS_IN_PRODUCT = """
    FOR s IN Serial
      FILTER s.product_key == @product_key
      RETURN s
  """

  GET_SERIALS_FOR_SERIAL_CODE = """
    FOR s IN Serial
      FILTER (@serial_key ? s._key != @serial_key : true) && UPPER(s.code) == UPPER(@serial)
      && s.product_key == @product_key
      && s.deleted == false
      RETURN s
  """

  GET_ALL_SERIALS_IN_WORK_ORDER = """
    FOR s IN Serial
      FILTER s.wo_key == @wo_key
      RETURN s
  """

  GET_AVAILABLE_WIP_SERIALS = """
    FOR w IN wip
      FILTER
        w.wo_key == @wo_key
        && (
          w._to == CONCAT('Phase/', @phase_key )
          || ( @job_key ? w._to == CONCAT('Job/', @job_key) : false ) // add wip allocated to job if job_key is provided
        )
      LET serial = DOCUMENT(Serial, w.serial_key)
      LET active = PARSE_IDENTIFIER(w._to).collection == 'Job'
      SORT serial.code
      RETURN MERGE(KEEP(serial, '_key', 'code', 'counter_key'), { active })
  """

  GET_SERIALS_FOR_CODE = """
    FOR s IN Serial
      FILTER (s.code == @serial_code && s.product_key == @product_key)
      && s.deleted == False
      RETURN s
  """

  FIND_SERIALS = """

    FOR s IN Serial

    // FILTER BY DOCUMENT PROPERTIES
    FILTER
      // When filtering by document key, parameters will be arrays
      (@serial_key ? POSITION(@serial_key, s._key) : true)
      && (@serial_search ? CONTAINS(LOWER(s.code), LOWER(@serial_search)) : true)
      && (@created_by ? POSITION(@created_by[* RETURN CONCAT('User/', CURRENT)], s.created_by) : true)
      && (@time_created_from ? s.created >= @time_created_from : true)
      && (@time_created_to ? s.created <= @time_created_to : true)
      && (@include_deleted ? true : !s.deleted)
      && (@filter_unreleased ? s.released != null : true)
      && (@time_released_from ? s.released >= @time_released_from : true)
      && (@time_released_to ? s.released <= @time_released_to : true)
      && (@advanced_filters
        ? LENGTH(
            // This subquery returns match true/false for each filter
            FOR advanced_filter IN NOT_NULL(@advanced_filters.filters, [])
            FOR d IN NOT_NULL(s.data, [])
            FILTER d.custom_field_key == advanced_filter._key
            LET type = DOCUMENT(CustomField, d.custom_field_key).type
            FILTER (
              type == "text" ? CONTAINS(LOWER(d.value), LOWER(advanced_filter.value))
              : type == "choice" ? d.value._key == advanced_filter.value._key
              : type == "boolean" ? !!d.value
              : type == "files" ? !!LENGTH(d.value)
              : d.value == advanced_filter.value
            )
            RETURN 1
          ) >= (@advanced_filters.operator == "OR" ? 1 : LENGTH(@advanced_filters.filters))
        : true
      )

    LET grid_data = (
      FOR field_value IN NOT_NULL(s.data, [])
        FOR field IN NOT_NULL(@fields, [])
        FILTER
          field._key == field_value.form_field_key || field._key == field_value.custom_field_key
        RETURN MERGE(field, { value: field_value.value })
    )

    // FILTER BY LINKS

    // PRODUCT
    let product = FIRST(
        FOR product IN Product
        FILTER product._key == s.product_key
        RETURN product
    )

    FILTER
      (@product_key ? product._key IN @product_key : true)
      && (@product_code_search ? CONTAINS(LOWER(product.code), LOWER(@product_code_search)) : true)

    // FILTER BY COMPONENTS
    LET children=(
        FOR v, e IN 1..999 OUTBOUND s._id contains
            FILTER @contains ? (CONTAINS(LOWER(v.code), LOWER(@contains))) : true
            FILTER e.replaced == false
            RETURN v.code
        )

    LET parents=(
        FOR v, e IN 1..999 INBOUND s._id contains
            FILTER @is_contained_in ? (CONTAINS(LOWER(v.code), LOWER(@is_contained_in))) : true
            FILTER e.replaced == false
            RETURN v.code
        )

    FILTER @contains ? count(children)>0 : true
    FILTER @is_contained_in ? count(parents)>0 : true

    LET wo = FIRST(
      FOR wo IN WorkOrder
      FILTER wo._key == s.wo_key
      RETURN wo
    )

    FILTER
      (@work_order_search ? CONTAINS(LOWER(wo.wo_code), LOWER(@work_order_search)) : true)
      && (@project_search ? CONTAINS(LOWER(wo.project_code), LOWER(@project_search)) : true)

    // RETURN RESULTS, WITH LINKS IF REQUESTED
    LET base_result = MERGE(s, {
      product,
      grid_data,
      wo_code: wo.wo_code,
      project_code: wo.project_code
    })

    // LIMIT FILTERED RECORDS
    SORT base_result.@sort_by @sorting_order

    LIMIT @offset, @limit || null
    return base_result
  """

  BOOK_SERIAL_WIP = """
    FOR w IN wip
    FILTER w.serial_key IN @serial_keys
    UPDATE w WITH { _to: CONCAT('Job/', @job_key), active: true } IN wip
  """

  DELETE_BATCH_SERIALS = """
    FOR s IN 1..1 OUTBOUND CONCAT('Batch/', @batch_key) batch_serial
    SORT s.created DESC
    LIMIT @to_delete
    REMOVE s IN Serial
  """

  CLEANUP_SERIAL_BATCH_LINKS = """
    FOR bs IN batch_serial
    FILTER !DOCUMENT(bs._from) || !DOCUMENT(bs._to)
    REMOVE bs IN batch_serial
  """

  CLEANUP_COMPONENT_LINKS = """
    FOR c IN contains
    FILTER !DOCUMENT(c._from) || !DOCUMENT(c._to)
    REMOVE c IN contains
  """

  REMOVE_PHASE_DATA_FROM_SERIAL = """
    FOR s IN Serial
    FILTER s._key == @serial_key
    LET new_serial_data = (
      FOR form_field IN s.data
      RETURN form_field.phase_key IN @phase_keys
        ? MERGE(form_field, { value: null, batch_key: null })
        : form_field
    )
    UPDATE s WITH { data: new_serial_data } IN Serial
  """


def get_bom_components_requiring_traceability(product_key: str) -> list[BomLineRead]:
  """
  Get components from the product BOM that require traceability
  """
  try:
    # Use the utility function to get the BOM components
    bom_components = get_bom_from_db(db, product_key)

    # Filter for components that require traceability using a list comprehension
    return [component for component in bom_components if component.traceability_level]
  except Exception:
    # Log error but continue - this is supplementary information
    traceback.print_exc()
    return []

def search_children(serial_key, children):
  """
  Recursively search for a serial_key in the children hierarchy.
  """
  found = False
  for child in children:
    if child.get('serial_key') == serial_key:
      found = True
    elif 'children' in child:
      found = found or search_children(serial_key, child['children'])
  return found


def get_serial_child_nodes(parent: SerialTreeNode, serial_list: list[dict]) -> list[SerialTreeNode]:
  # If the parent serial is not confirmed or replaced, don't build the children
  if parent.confirmed == False or parent.replaced == True:
    return []

  components = get_bom_components_requiring_traceability(parent.product_key)
  children = []
  try:
    # First, handle BOM components
    for component in components:
      bom_node_base_data = dict(
        product_key=component.component_key,
        product_code=component.component_code,
        product_description=component.component_description
      )

      child_serials = [s for s in serial_list
        if s['product_key'] == component.component_key
        and s['parent_key'] == parent.serial_key
      ]

      if len(child_serials) > 0:
        for child_serial in child_serials:
          child_node = SerialTreeNode(
            **bom_node_base_data,
            # Add serial data to the child node
            serial_key = child_serial['serial_key'],
            serial_code = child_serial['serial_code'],
            replaced = child_serial.get('replaced', False),
            confirmed = child_serial.get('confirmed', True)
          )
          # Recursively build the child node's children
          if child_serial.get('replaced') == False:
            child_node.children = get_serial_child_nodes(child_node, serial_list)

          # Add the child node to the start node's children
          children.append(child_node)

      # If there are no active child serials, add an empty node for the component
      if sum(1 for child in child_serials if child.get('replaced') == False) == 0:
        children.append(SerialTreeNode(**bom_node_base_data))

    # Then, handle non-BOM serials that are children of this parent
    bom_component_keys = [comp.component_key for comp in components]
    non_bom_serials = [
      s for s in serial_list
      if s['parent_key'] == parent.serial_key and
      s['product_key'] not in bom_component_keys
    ]

    for serial in non_bom_serials:
      child_node = SerialTreeNode(
        product_key=serial['product_key'],
        product_code=serial['product_code'],
        product_description=serial['product_description'],
        serial_key=serial['serial_key'],
        serial_code=serial['serial_code'],
        replaced=serial.get('replaced', False),
        confirmed=serial.get('confirmed', True),
        extra_bom=True
      )
      child_node.children = get_serial_child_nodes(child_node, serial_list)
      children.append(child_node)

    return children

  except Exception:
    traceback.print_exc()
    raise


# DHR (Device History Record) utility functions

def fetch_dhr_data(serial_key: str) -> Dict[str, Any]:
  """Fetch serial and product data for DHR generation"""
  aql = """
    LET s = DOCUMENT(Serial, @serial_key)
    FILTER s != null
    LET product = s.product_key ? DOCUMENT(Product, s.product_key) : null
    LET wo = s.wo_key ? DOCUMENT(WorkOrder, s.wo_key) : null
    LET fields = (
      FOR d IN NOT_NULL(s.data, [])
        LET cf = d.custom_field_key ? DOCUMENT(CustomField, d.custom_field_key) : null
        LET label = d.label ? d.label : (cf ? (cf.default_label ? cf.default_label : cf.name) : '')
        LET phase = d.phase_key ? DOCUMENT(Phase, d.phase_key) : null
        LET last_event = d.last_updated ? DOCUMENT(Event, d.last_updated) : null
        LET last_user = last_event && last_event.user_key ? DOCUMENT(User, last_event.user_key) : null
        RETURN {
          label,
          form_field_key: d.form_field_key,
          value: d.value,
          phase_key: d.phase_key,
          phase_alias: phase ? (phase.alias || phase.code || phase._key) : null,
          field_type: cf ? cf.type : null,
          last_updated_ts: last_event ? last_event.timestamp : null,
          last_updated_user: last_user ? { name: last_user.name, surname: last_user.surname } : null
        }
    )
    RETURN {
      serial: { code: s.code, created: s.created, released: s.released },
      product_code: product ? product.code : null,
      product_description: product ? product.description : null,
      wo_phase_sequence: wo ? wo.phase_sequence : [],
      fields
    }
  """
  result = list(db.aql.execute(aql, bind_vars=dict(serial_key=serial_key)))
  if not result:
    return {}
  return result[0]


def safe_text(value) -> str:
  """Convert various data types to safe text for display"""
  if value is None:
    return ''
  if isinstance(value, (int, float)):
    return str(value)
  if isinstance(value, str):
    return value
  # choices or other dicts
  if isinstance(value, dict):
    return value.get('value') or value.get('name') or json.dumps(value)
  # files or generic lists
  if isinstance(value, list):
    try:
      # if files: list of {name, size}
      names = [v.get('name') if isinstance(v, dict) else str(v) for v in value]
      return ', '.join([n for n in names if n])
    except Exception:
      return json.dumps(value)
  return str(value)


def format_minute(iso_ts) -> str:
  """Format timestamp to 'YYYY-MM-DD HH:MM' format"""
  if iso_ts is None:
    return ''
  try:
    if isinstance(iso_ts, str):
      # Basic truncation and T replacement, safe fallback
      return iso_ts.replace('T', ' ')[:16]
    # if datetime
    from datetime import datetime as _dt
    if isinstance(iso_ts, _dt):
      return iso_ts.strftime('%Y-%m-%d %H:%M')
    # numeric epoch milliseconds or seconds
    if isinstance(iso_ts, (int, float)):
      import math
      seconds = iso_ts / 1000 if iso_ts > 1e12 else iso_ts
      from datetime import datetime as _dt2
      return _dt2.utcfromtimestamp(seconds).strftime('%Y-%m-%d %H:%M')
  except Exception:
    pass
  return str(iso_ts)


def get_checkbox_svgs() -> Dict[str, str]:
  """Get SVG definitions for checkbox states"""
  return {
    'checked': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '<path d="M4 8l3 3 5-6" stroke="#111" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
      '</svg>'
    ),
    'unchecked': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '</svg>'
    ),
    'indeterminate': (
      '<svg width="12" height="12" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" style="vertical-align:middle">'
      '<rect x="1" y="1" width="14" height="14" fill="#fff" stroke="#333" stroke-width="1.5"/>'
      '<path d="M4 8h8" stroke="#111" stroke-width="2"/>'
      '</svg>'
    )
  }


def process_fields_for_display(fields: List[Dict], wo_phase_sequence: List[str]) -> Tuple[str, bool]:
  """Process fields and group them by phase for display"""
  checkbox_svgs = get_checkbox_svgs()

  # Group fields by phase and build rows with phase alias headers
  fields_by_phase = {}
  phase_alias_map = {}

  for field in fields:
    label = field.get('label') or ''
    field_type = (field.get('field_type') or '').lower()
    value = field.get('value')

    if field_type in ('boolean', 'ternary'):
      if value is True:
        value_html = checkbox_svgs['checked']
      elif value is False:
        value_html = checkbox_svgs['unchecked']
      else:
        value_html = checkbox_svgs['indeterminate']
    else:
      value_html = safe_text(value)

    last_minute = format_minute(field.get('last_updated_ts'))
    lu = field.get('last_updated_user') or {}
    if isinstance(lu, dict):
      last_user_name = f"{(lu.get('name') or '').strip()} {(lu.get('surname') or '').strip()}".strip()
    else:
      last_user_name = ''

    phase_key = field.get('phase_key')
    if phase_key not in fields_by_phase:
      fields_by_phase[phase_key] = []
    if phase_key and phase_key not in phase_alias_map:
      phase_alias_map[phase_key] = field.get('phase_alias') or phase_key

    fields_by_phase[phase_key].append({
      'label': label,
      'value_html': value_html,
      'last_updated': last_minute,
      'last_user': last_user_name
    })

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in fields_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in fields_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Build grouped rows HTML and check if we have any data
  rows_html = ''
  has_serial_data = len(fields) > 0

  if None in fields_by_phase:
    rows_html += f"""
      <tr>
        <th class="phase-header" colspan="4">General</th>
      </tr>
    """
    for item in fields_by_phase[None]:
      rows_html += f"""
        <tr>
          <td class="cell">{item['label']}</td>
          <td class="cell">{item['value_html']}</td>
          <td class="cell">{item['last_updated']}</td>
          <td class="cell">{item['last_user']}</td>
        </tr>
      """

  for pk in ordered_phase_keys:
    phase_title = phase_alias_map.get(pk, pk)
    rows_html += f"""
      <tr>
        <th class="phase-header" colspan="4">{phase_title}</th>
      </tr>
    """
    for item in fields_by_phase.get(pk, []):
      rows_html += f"""
        <tr>
          <td class="cell">{item['label']}</td>
          <td class="cell">{item['value_html']}</td>
          <td class="cell">{item['last_updated']}</td>
          <td class="cell">{item['last_user']}</td>
        </tr>
      """

  return rows_html, has_serial_data


def generate_children_tables(serial_key: str) -> Tuple[str, str]:
  """Generate HTML for simple and complex children tables"""
  simple_children_table_html = ''
  complex_children_list_html = ''

  try:
    bind_vars = dict(serial_id=f'Serial/{serial_key}')
    children_result = list(db.aql.execute(Queries.GET_SERIAL_CHILDREN_FOR_DHR, bind_vars=bind_vars))

    if children_result:
      # Sort children by product code first, then serial code
      children_result.sort(key=lambda x: (x.get('product_code') or '', x.get('serial_code') or ''))

      # Separate children into simple (no data, no children) and complex (with data or children)
      simple_children = [child for child in children_result if not child.get('has_data') and not child.get('has_children')]
      complex_children = [child for child in children_result if child.get('has_data') or child.get('has_children')]

      # Create table for simple children
      if simple_children:
        simple_children_table_html = '''
        <h2>Component Serials</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Product Code</th>
              <th>Product Description</th>
              <th>Serial Code</th>
            </tr>
          </thead>
          <tbody>'''
        for child in simple_children:
          child_serial_code = child.get('serial_code') or ''
          child_product_code = child.get('product_code') or ''
          child_product_description = child.get('product_description') or ''
          simple_children_table_html += f'''
            <tr>
              <td class="cell">{child_product_code}</td>
              <td class="cell">{child_product_description}</td>
              <td class="cell">{child_serial_code}</td>
            </tr>'''
        simple_children_table_html += '''
          </tbody>
        </table>'''

      # Create list for complex children
      if complex_children:
        complex_children_list_html = '<h2 class="small-heading">Child Serials with Detailed Data</h2>'
        complex_children_list_html += '<p class="small-text"><em>The following child serials contain detailed data or sub-components. Their complete Device History Records are included on the following pages.</em></p>'
        complex_children_list_html += '<ul>'
        for child in complex_children:
          child_serial_code = child.get('serial_code') or ''
          child_product_code = child.get('product_code') or ''
          child_product_description = child.get('product_description') or ''
          complex_children_list_html += f'<li><strong>{child_product_code}</strong> - {child_product_description} - {child_serial_code}</li>'
        complex_children_list_html += '</ul>'
  except Exception:
    pass

  return simple_children_table_html, complex_children_list_html


def generate_dhr_html(serial_key: str, data: Dict[str, Any]) -> str:
  """Generate HTML content for DHR"""
  serial_info = data.get('serial') or {}
  serial_code = serial_info.get('code') or ''
  product_code = data.get('product_code') or ''
  product_description = data.get('product_description') or ''
  created = serial_info.get('created') or ''
  released = serial_info.get('released') or ''
  fields = data.get('fields') or []
  wo_phase_sequence = data.get('wo_phase_sequence') or []

  # Process fields for display
  rows_html, has_serial_data = process_fields_for_display(fields, wo_phase_sequence)

  # Build serial data table HTML only if there is data
  serial_data_table_html = ''
  if has_serial_data:
    serial_data_table_html = f"""
        <h2>Serial Data</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Field</th>
              <th>Value</th>
              <th>Last update</th>
              <th>User</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>"""

  # Generate children tables
  simple_children_table_html, complex_children_list_html = generate_children_tables(serial_key)

  html = f"""
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          @page {{ margin: 20mm 15mm; }}
          body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif; color: #222; }}
          h1 {{ font-size: 18px; margin: 0 0 8px 0; }}
          h2 {{ font-size: 14px; margin: 16px 0 8px 0; }}
          h3 {{ font-size: 12px; margin: 12px 0 6px 0; }}
          .meta {{ font-size: 12px; margin-bottom: 12px; }}
          .table {{ width: 100%; border-collapse: collapse; }}
          .table th {{ text-align: left; font-size: 12px; border-bottom: 1px solid #ccc; padding: 6px 4px; }}
          .cell {{ font-size: 12px; border-bottom: 1px solid #eee; padding: 6px 4px; vertical-align: top; }}
          .phase-header {{ font-size: 12px; background-color: #f6f6f6; border-top: 1px solid #ccc; border-bottom: 1px solid #ccc; padding: 8px 4px; }}
          .small-heading {{ font-size: 12px; margin: 16px 0 8px 0; }}
          .small-text {{ font-size: 12px; margin: 8px 0; }}
          ul {{ margin: 8px 0; padding-left: 20px; }}
          li {{ font-size: 12px; margin: 2px 0; }}
        </style>
      </head>
      <body>
        <h1>Device History Record</h1>
        <div class="meta">
          <div><strong>Serial Key:</strong> {serial_key}</div>
          <div><strong>Serial Code:</strong> {serial_code}</div>
          <div><strong>Product Code:</strong> {product_code}</div>
          <div><strong>Product Description:</strong> {product_description}</div>
          <div><strong>Created:</strong> {created}</div>
          <div><strong>Released:</strong> {released}</div>
        </div>
        {serial_data_table_html}
        {simple_children_table_html}
        {complex_children_list_html}
      </body>
    </html>
  """

  return html


def collect_attachments(fields: List[Dict], serial_key: str, include_attachments: bool) -> List[Dict]:
  """Collect file attachments from serial fields with metadata including phase information"""
  attachments: List[Dict] = []

  if not include_attachments:
    return attachments

  print(f"🔍 DEBUG: Starting attachment collection for serial {serial_key}")
  media_root = get_config().media_path
  print(f"🔍 DEBUG: Media root path: {media_root}")
  image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp'}

  # Build a list of attachment dictionaries with metadata
  print(f"🔍 DEBUG: Total fields to check: {len(fields)}")
  file_fields_count = 0

  for f in fields:
    field_type = (f.get('field_type') or '').lower()
    if field_type != 'files':
      continue

    file_fields_count += 1
    print(f"🔍 DEBUG: Found file field {file_fields_count}: {f.get('label', 'N/A')}")
    form_field_key = f.get('form_field_key') or ''
    field_label = f.get('label') or ''
    phase_alias = f.get('phase_alias') or ''
    phase_key = f.get('phase_key') or ''
    print(f"🔍 DEBUG: Form field key: '{form_field_key}', Phase: '{phase_alias}' (key: '{phase_key}'), Field: '{field_label}'")
    print(f"🔍 DEBUG: Full field data: {f}")
    value = f.get('value')
    print(f"🔍 DEBUG: Field value type: {type(value)}, value: {value}")

    if not value:
      print(f"🔍 DEBUG: No value in field, skipping")
      continue

    # value expected to be a list of dicts with 'name'
    try:
      if isinstance(value, list):
        print(f"🔍 DEBUG: Processing {len(value)} items in value list")
        for i, item in enumerate(value):
          filename = None
          if isinstance(item, dict):
            filename = item.get('name')
            print(f"🔍 DEBUG: Item {i+1} is dict, filename: {filename}")
          elif isinstance(item, str):
            filename = item
            print(f"🔍 DEBUG: Item {i+1} is string, filename: {filename}")
          else:
            print(f"🔍 DEBUG: Item {i+1} unexpected type: {type(item)}")

          if not filename:
            print(f"🔍 DEBUG: No filename for item {i+1}, skipping")
            continue

          file_path = os.path.join(media_root, 'serial', serial_key, form_field_key, filename)
          ext = os.path.splitext(filename)[1].lower()
          file_exists = os.path.exists(file_path)

          print(f"🔍 DEBUG: File {i+1}: {filename}")
          print(f"🔍 DEBUG: Extension: {ext}")
          print(f"🔍 DEBUG: Full path: {file_path}")
          print(f"🔍 DEBUG: File exists: {file_exists}")

          if ext == '.pdf' or ext in image_exts:
            attachment_type = 'pdf' if ext == '.pdf' else 'image'
            attachment_data = {
              'path': file_path,
              'type': attachment_type,
              'filename': filename,
              'field_label': field_label,
              'phase_alias': phase_alias or 'General',  # Fallback to 'General' if phase_alias is empty
              'phase_key': phase_key
            }
            attachments.append(attachment_data)
            print(f"🔍 DEBUG: Added {attachment_type} attachment: {filename} (Phase: '{phase_alias}' -> '{attachment_data['phase_alias']}', Field: '{field_label}')")
          else:
            print(f"🔍 DEBUG: Unsupported file type: {ext}")
      else:
        print(f"🔍 DEBUG: Value is not a list, type: {type(value)}")
    except Exception as e:
      print(f"🔍 DEBUG: Exception processing field: {e}")
      # If format is unexpected, skip
      pass

  print(f"🔍 DEBUG: File fields found: {file_fields_count}")
  print(f"🔍 DEBUG: Total attachments collected: {len(attachments)}")
  for i, attachment in enumerate(attachments):
    print(f"🔍 DEBUG: Attachment {i+1}: {attachment['type']} - {attachment['filename']} (Phase: {attachment['phase_alias']}, Field: {attachment['field_label']})")

  return attachments


async def process_image_attachments(context, image_attachments: List[Dict], serial_info_for_headers: str, wo_phase_sequence: List[str]) -> List[bytes]:
  """Process image attachments grouped by phase and return list of PDF bytes"""
  pdf_pages = []

  if not image_attachments:
    return pdf_pages

  print(f"🔍 DEBUG: Processing {len(image_attachments)} images grouped by phase")

  # Group images by phase
  images_by_phase = {}
  for attachment in image_attachments:
    phase_key = attachment.get('phase_key') or None
    if phase_key not in images_by_phase:
      images_by_phase[phase_key] = []
    images_by_phase[phase_key].append(attachment)

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in images_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in images_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Add None phase (general) at the beginning if it exists
  if None in images_by_phase:
    ordered_phase_keys.insert(0, None)

  # Process each phase group
  for phase_key in ordered_phase_keys:
    phase_images = images_by_phase[phase_key]
    if not phase_images:
      continue

    # Get phase title
    if phase_key:
      # Try to get a meaningful phase title with multiple fallbacks
      phase_title = (
        phase_images[0].get('phase_alias') or
        phase_images[0].get('phase_key') or
        phase_key or
        "Unknown Phase"
      )
    else:
      phase_title = "General"

    print(f"🔍 DEBUG: Processing {len(phase_images)} images for phase: {phase_title}")

    # Process images in groups of 2 per page
    for page_num in range(0, len(phase_images), 2):
      images_on_page = phase_images[page_num:page_num + 2]
      print(f"🔍 DEBUG: Creating image page {page_num//2 + 1} for phase {phase_title} with {len(images_on_page)} images")

      try:
        # Prepare image data for both images
        image_data_list = []
        for attachment in images_on_page:
          img_path = attachment['path']
          try:
            print(f"🔍 DEBUG: Reading image: {img_path}")
            with open(img_path, 'rb') as imgf:
              file_data = imgf.read()
              print(f"🔍 DEBUG: Read {len(file_data)} bytes from {attachment['filename']}")
              b64 = base64.b64encode(file_data).decode('ascii')
              ext = os.path.splitext(img_path)[1].lower()
              mime = 'image/png'
              if ext == '.jpg' or ext == '.jpeg':
                mime = 'image/jpeg'
              elif ext == '.webp':
                mime = 'image/webp'
              elif ext == '.gif':
                mime = 'image/gif'
              elif ext == '.bmp':
                mime = 'image/bmp'

              image_data_list.append({
                'filename': attachment['filename'],
                'field_label': attachment['field_label'],
                'b64': b64,
                'mime': mime
              })
          except Exception as e:
            print(f"🔍 DEBUG: Error reading image {img_path}: {e}")
            continue

        if not image_data_list:
          print(f"🔍 DEBUG: No valid images for this page, skipping")
          continue

        # Create HTML for 1 or 2 images
        images_html = ""
        for i, img_data in enumerate(image_data_list):
          display_name = f"{img_data['field_label']} - {img_data['filename']}" if img_data['field_label'] else img_data['filename']
          images_html += f"""
            <div class="image-container">
              <div class="filename">{display_name}</div>
              <img src="data:{img_data['mime']};base64,{img_data['b64']}" />
            </div>
          """

        # Determine page title
        page_title = f"Attachments - {phase_title}"
        if len(phase_images) > 2:
          page_start = page_num + 1
          page_end = min(page_num + 2, len(phase_images))
          page_title += f" ({page_start}-{page_end}/{len(phase_images)})"

        img_html = f"""
          <html>
            <head>
              <meta charset='utf-8' />
              <style>
                @page {{ margin: 15mm 10mm 15mm 10mm; }}
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif; color: #222; margin: 0; padding: 0; }}
                .header {{ text-align: center; border-bottom: 1px solid #ccc; padding-bottom: 8px; margin-bottom: 15px; }}
                .header h2 {{ font-size: 16px; margin: 0 0 4px 0; }}
                .header .serial-info {{ font-size: 12px; color: #666; margin: 0; }}
                .images-container {{ display: flex; flex-direction: column; gap: 15px; height: calc(100vh - 60px); }}
                .image-container {{ text-align: center; flex: 1; display: flex; flex-direction: column; }}
                .filename {{ font-size: 11px; margin-bottom: 8px; font-weight: bold; }}
                img {{ max-height: calc((100vh - 120px) / {len(image_data_list)}); max-width: 100%; object-fit: contain; }}
              </style>
            </head>
            <body>
              <div class="header">
                <h2>{page_title}</h2>
                <div class="serial-info">{serial_info_for_headers}</div>
              </div>
              <div class="images-container">
                {images_html}
              </div>
            </body>
          </html>
        """

        img_page = await context.new_page()
        await img_page.set_content(img_html, wait_until='load')
        img_pdf_bytes = await img_page.pdf(
          format='A4',
          print_background=True,
          margin={'top': '15mm', 'bottom': '15mm', 'left': '10mm', 'right': '10mm'}
        )
        await img_page.close()
        pdf_pages.append(img_pdf_bytes)
        print(f"🔍 DEBUG: Successfully created PDF for {len(image_data_list)} images in phase {phase_title}")

      except Exception as e:
        print(f"🔍 DEBUG: Error creating image page for phase {phase_title}: {e}")
        continue

  return pdf_pages


def process_pdf_attachments(pdf_attachments: List[Dict], serial_info_for_headers: str, wo_phase_sequence: List[str]) -> List[bytes]:
  """Process PDF attachments grouped by phase and return list of processed PDF bytes"""
  processed_pdfs = []

  if not pdf_attachments:
    return processed_pdfs

  print(f"🔍 DEBUG: Processing {len(pdf_attachments)} PDFs grouped by phase")

  # Group PDFs by phase
  pdfs_by_phase = {}
  for attachment in pdf_attachments:
    phase_key = attachment.get('phase_key') or None
    if phase_key not in pdfs_by_phase:
      pdfs_by_phase[phase_key] = []
    pdfs_by_phase[phase_key].append(attachment)

  # Order phases by work order phase sequence when available
  ordered_phase_keys = []
  for k in wo_phase_sequence:
    if k in pdfs_by_phase and k not in ordered_phase_keys:
      ordered_phase_keys.append(k)
  for k in [k for k in pdfs_by_phase.keys() if k]:
    if k not in ordered_phase_keys:
      ordered_phase_keys.append(k)

  # Add None phase (general) at the beginning if it exists
  if None in pdfs_by_phase:
    ordered_phase_keys.insert(0, None)

  # Process each phase group
  for phase_key in ordered_phase_keys:
    phase_pdfs = pdfs_by_phase[phase_key]
    if not phase_pdfs:
      continue

    # Get phase title
    if phase_key:
      # Try to get a meaningful phase title with multiple fallbacks
      phase_title = (
        phase_pdfs[0].get('phase_alias') or
        phase_pdfs[0].get('phase_key') or
        phase_key or
        "Unknown Phase"
      )
    else:
      phase_title = "General"

    print(f"🔍 DEBUG: Processing {len(phase_pdfs)} PDFs for phase: {phase_title}")

    for i, attachment in enumerate(phase_pdfs):
      path_str = attachment['path']
      print(f"🔍 DEBUG: Processing PDF attachment {i+1}: {attachment['filename']} (Phase: {phase_title})")

      try:
        print(f"🔍 DEBUG: Opening PDF file: {path_str}")
        with open(path_str, 'rb') as pf:
          attach_reader = PdfReader(pf)
          num_pages = len(attach_reader.pages)
          print(f"🔍 DEBUG: PDF has {num_pages} pages")

          # Create a new writer for this PDF with headers
          writer = PdfWriter()

          # Draw each original page inside a framed area on A4 with header
          page_width, page_height = A4
          left_margin = 15 * mm
          right_margin = 15 * mm
          bottom_margin = 15 * mm
          top_margin = 35 * mm  # Increased for 3-line header
          header_area = 28 * mm  # Increased for 3-line header
          frame_left = float(left_margin)
          frame_bottom = float(bottom_margin)
          frame_right = float(page_width - right_margin)
          frame_top = float(page_height - (top_margin + header_area))
          frame_width = frame_right - frame_left
          frame_height = frame_top - frame_bottom

          filename = attachment['filename']
          field_label = attachment['field_label']

          for idx, original_page in enumerate(attach_reader.pages):
            # Create overlay with header and border
            overlay_buf = io.BytesIO()
            c = canvas.Canvas(overlay_buf, pagesize=A4)

            # Draw 3-line header
            header_y_line1 = float(page_height - top_margin - 4)
            header_y_line2 = float(page_height - top_margin - 16)
            header_y_line3 = float(page_height - top_margin - 26)

            c.setFont("Helvetica-Bold", 16)
            c.drawString(float(left_margin), header_y_line1, f"Attachments - {phase_title}")
            c.setFont("Helvetica", 12)
            c.drawString(float(left_margin), header_y_line2, f"{serial_info_for_headers}")

            # Draw field label and filename info
            if field_label:
              c.setFont("Helvetica", 10)
              c.drawString(float(left_margin), header_y_line3, f"Field: {field_label}")

            # Draw filename and page number on the right
            c.setFont("Helvetica", 9)
            filename_text = f"{filename} - Page {idx+1}/{num_pages}"
            text_width = c.stringWidth(filename_text)
            c.drawString(float(frame_right - text_width), header_y_line3, filename_text)

            # Draw border around content area
            c.setLineWidth(1)
            c.rect(frame_left, frame_bottom, frame_width, frame_height, stroke=1, fill=0)
            c.showPage()
            c.save()
            overlay_buf.seek(0)
            overlay_reader = PdfReader(overlay_buf)
            overlay_page = overlay_reader.pages[0]

            # Fit original page inside frame while preserving aspect
            orig_w = float(original_page.mediabox.width)
            orig_h = float(original_page.mediabox.height)
            scale = min(frame_width / orig_w, frame_height / orig_h)
            scaled_w = orig_w * scale
            scaled_h = orig_h * scale
            translate_x = frame_left + (frame_width - scaled_w) / 2
            translate_y = frame_bottom + (frame_height - scaled_h) / 2

            transformation = Transformation().scale(scale).translate(tx=translate_x, ty=translate_y)
            overlay_page.merge_transformed_page(original_page, transformation)
            writer.add_page(overlay_page)

          # Convert writer to bytes
          output = io.BytesIO()
          writer.write(output)
          output.seek(0)
          processed_pdfs.append(output.getvalue())
          print(f"🔍 DEBUG: Successfully processed PDF {filename} with {num_pages} pages for phase {phase_title}")

      except Exception as e:
        print(f"🔍 DEBUG: Error processing PDF {path_str}: {e}")
        continue

  return processed_pdfs


async def generate_dhr_for_serial(serial_key: str, context, include_attachments: bool = False) -> bytes:
  """Generate a DHR PDF for a specific serial"""
  try:
    # Fetch serial and product data
    data = fetch_dhr_data(serial_key)
    if not data:
      return b''

    # Generate HTML content
    html = generate_dhr_html(serial_key, data)

    # Convert main content to PDF
    page = await context.new_page()
    await page.set_content(html, wait_until='load')
    main_pdf_bytes = await page.pdf(
      format='A4',
      print_background=True,
      margin={'top': '20mm', 'bottom': '20mm', 'left': '15mm', 'right': '15mm'}
    )
    await page.close()

    # If no attachments requested, return the main PDF
    if not include_attachments:
      return main_pdf_bytes

    # Create a PDF writer to combine main content with attachments
    writer = PdfWriter()
    main_reader = PdfReader(io.BytesIO(main_pdf_bytes))
    for pg in main_reader.pages:
      writer.add_page(pg)

    # Collect and process attachments
    fields = data.get('fields', [])
    attachments = collect_attachments(fields, serial_key, include_attachments)

    if not attachments:
      print(f"🔍 DEBUG: No attachments to process")
      return main_pdf_bytes

    # Get serial info for attachment headers
    serial_info = data.get('serial') or {}
    product_code = data.get('product_code') or ''
    serial_code = serial_info.get('code') or ''
    serial_info_for_headers = f"{product_code} - {serial_code}" if product_code and serial_code else serial_key
    wo_phase_sequence = data.get('wo_phase_sequence', [])

    # Separate image and PDF attachments
    image_attachments = [attachment for attachment in attachments if attachment['type'] == 'image']
    pdf_attachments = [attachment for attachment in attachments if attachment['type'] == 'pdf']

    # Process image attachments
    if image_attachments:
      image_pdf_pages = await process_image_attachments(context, image_attachments, serial_info_for_headers, wo_phase_sequence)
      for img_pdf_bytes in image_pdf_pages:
        img_reader = PdfReader(io.BytesIO(img_pdf_bytes))
        for pg in img_reader.pages:
          writer.add_page(pg)

    # Process PDF attachments
    if pdf_attachments:
      processed_pdf_bytes_list = process_pdf_attachments(pdf_attachments, serial_info_for_headers, wo_phase_sequence)
      for pdf_bytes in processed_pdf_bytes_list:
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        for pg in pdf_reader.pages:
          writer.add_page(pg)

    # Return combined PDF
    total_pages = len(writer.pages)
    print(f"🔍 DEBUG: Final PDF has {total_pages} total pages")
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    final_size = len(output.getvalue())
    print(f"🔍 DEBUG: Final PDF size: {final_size} bytes")
    return output.getvalue()

  except Exception:
    return b''

