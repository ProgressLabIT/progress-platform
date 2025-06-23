import traceback

from models.bom import BomLineRead
from models.serial import SerialTreeNode
from utils.bom import get_bom_from_db
from utils.db import db

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

