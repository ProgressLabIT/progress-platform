from models.inventory import InventoryMovementReferences

class Queries:

  PRODUCTS_INVENTORY_CONFIG = """
    RETURN MERGE(
      FOR p IN Product
      FILTER p._key IN @product_keys
      RETURN { [p._key]: p.manage_inventory }
    )
  """

  SEARCH_POSITIONS = """
    LET start = CONCAT('Position/', NOT_NULL(@is_in_position, 'IN'))

    FOR v, e, p IN 1..99 INBOUND start is_in_position

    FILTER
      IS_SAME_COLLECTION('Position', v)
      && (@position_keys ? v._key IN @position_keys : true)
      && (@contains_position ? @contains_position IN p.vertices[*]._key : true)
      && (@search ? LOWER(v.code) LIKE CONCAT('%', LOWER(@search), '%') : true)
      && (@has_product_key ? @has_product_key == p.vertices[-1]._key : true)
      && (@has_product_code ? @has_product_code == p.vertices[-1].code : true)

    LIMIT @offset, @limit || null

    RETURN v
  """

  GET_POSITION_CONTENTS = """
    FOR v, e IN 1..1 INBOUND CONCAT('Position/', @position_key) is_in_position OPTIONS { uniqueVertices: "path" }
    LET position = (IS_SAME_COLLECTION(Position, v)) ? MERGE({ type: 'position' }, v) : null
    LET product = IS_SAME_COLLECTION(Product, v) ? MERGE({ type: 'product', quantity: e.quantity }, v) : null
    LET serial = e.serial_key ? FIRST(
      FOR s IN Serial
      FILTER s._key == e.serial_key
      RETURN MERGE({ type: 'serial', product_code: v.code }, s)
    ): null
    LET result = NOT_NULL(serial, product, position)
    FILTER result != null && result.code != null
    FILTER @search ? (CONTAINS(LOWER(result.code), LOWER(@search)) || CONTAINS(LOWER(result.product_code), LOWER(@search))) : true
    SORT result.code ASC
    LIMIT @limit
    RETURN {
      _key: e._key,
      type: result.type,
      code: result.code,
      position_key: result.type == 'position' ? v._key : null,
      position_fixed: result.type == 'position' ? v.fixed : null,
      product_code: result.type == 'position' ? null : v.code,
      product_key: result.type == 'position' ? null : v._key,
      quantity: e.quantity,
      serial_code: result.type == 'serial' ? serial.code : null,
      serial_key: result.type == 'serial' ? serial._key : null,
    }
  """

  INVENTORY_FILTER = """
    // POSITION
      let position = FIRST(
          FOR position IN Position
          FILTER position._id == e._to
          RETURN position
      )

    // SERIAL
      let serial = FIRST(
          FOR serial IN Serial
          FILTER serial._key == e.serial_key
          RETURN serial
      )

    FILTER
      IS_SAME_COLLECTION('Product', v)
      && (@position_key ? position._key == @position_key : true)
      && (@position_code ? position.code == @position_code : true)
      && (@serial_code ? serial.code == @serial_code : true)
      && (@position_search ? CONTAINS(LOWER(position.code), LOWER(@position_search)) : true)
      && (@product_search ? CONTAINS(LOWER(v.code), LOWER(@product_search)) : true)
      && (@serial_search ? CONTAINS(LOWER(serial.code), LOWER(@serial_search)) : true)
      && (@product_key ? v._key == @product_key : true)
      && (@product_code ? v.code == @product_code : true)
      && (@owned ? e.owned == @owned : true)
      && (@serial_keys ? e.serial_key IN @serial_keys : @strict ? e.serial_key == null : true)
      //&& (@contains_position ? @contains_position IN p.vertices[*]._key : true)
      //&& (@search ? LOWER(v.code) LIKE CONCAT('%', LOWER(@search), '%') : true)
      //&& (@has_product_key ? @has_product_key == p.vertices[-1]._key : true)
      //&& (@has_product_code ? @has_product_code == p.vertices[-1].code : true)
  """

  SEARCH_INVENTORY = """
    FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """

    COLLECT pos = position, product = v, ser = serial, owned = e.owned
    AGGREGATE quantity = SUM(e.quantity), value = SUM(e.value)
    LIMIT @offset, @limit || null


    RETURN {
      product_id: product._id,
      product_code: product.code,
      position_id: pos._id,
      position_key: pos._key,
      position_code: pos.code,
      serial_key: ser._key,
      serial_code: ser.code,
      quantity,
      owned,
      value
    }
  """

  SEARCH_INVENTORY_GRAPH = """
    FOR product IN Product
    FILTER @product_key ? product._key == @product_key : true
    SORT product.code
    LET context = CONCAT(product.code, ' ', product.description)
    FILTER @product_search ? CONTAINS(LOWER(context), LOWER(@product_search)) : true

    LET start = @root_position_key ? DOCUMENT(Position, @root_position_key) : DOCUMENT('Position/IN')
    FOR path IN 1..99 INBOUND K_PATHS start TO product._id is_in_position
      LET inventory = LAST(path.edges)
      FILTER @owned ? inventory.owned : true
      FILTER @serial_keys ? inventory.serial_key IN @serial_keys : true
      LET serial_code = DOCUMENT(Serial, inventory.serial_key).code
      FILTER @serial_search ? CONTAINS(LOWER(serial_code), LOWER(@serial_search)) : true
      LIMIT @offset || 0, @limit || null
      LET p = (
        FOR vertex IN SHIFT(POP(path.vertices)) // Exclude root position IN and final product vertex
        RETURN {
          position_key: vertex._key,
          position_code: vertex.code
        }
      )

      LET shown_path = LENGTH(p) == 0 ? [{ position_key: start._key, position_code: start.code }] : p
      FILTER @position_search
        ? shown_path[? ANY FILTER CONTAINS(LOWER(CURRENT.position_code), LOWER(@position_search))]
        : true

      RETURN {
        // Show root position in case the product is there (no path)
        path: shown_path,
        quantity: inventory.quantity,
        serial_key: inventory.serial_key,
        product_key: product._key,
        product_code: product.code,
        product_desc: product.description,
        serial_code,
        value: inventory.value,
        _key: inventory._key
    }
  """

  SEARCH_INVENTORY_PRODUCT = """
     FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """

    LIMIT @offset, @limit || null

    RETURN DISTINCT v
  """

  SEARCH_INVENTORY_POSITIONS = """
     FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """

    LIMIT @offset, @limit || null

      RETURN DISTINCT position
  """

  SEARCH_INVENTORY_SERIALS = """
     FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """
      && e.serial_key != null

    LIMIT @offset, @limit || null



      RETURN DISTINCT MERGE (serial, {
          label: serial.code,
          value: serial._key
      })
  """

  GET_POSITION_HIERARCHY = """
    LET start = @position_id

    LET ancestors = (
        FOR v, e IN 0..9999 OUTBOUND start is_in_position OPTIONS { uniqueVertices: "path" }
        RETURN {
            position_id: v._id,
            position_key: v._key,
            code: v.code,
            product_key: v.product_key,
            from: e._from,
            to: e._to
        }
    )

    LET descendants = (
        FOR v, e IN 0..9999 INBOUND start is_in_position OPTIONS { uniqueVertices: "path" }
        FILTER IS_SAME_COLLECTION(Position, v)
        RETURN {
            position_id: v._id,
            position_key: v._key,
            code: v.code,
            product_key: v.product_key,
            from: e._from,
            to: e._to
        }
    )

    FOR p in UNION_DISTINCT(ancestors, descendants)
    RETURN p
  """

  GET_POSITION_CHILDREN_COUNT = """
    LET start = CONCAT('Position/', NOT_NULL(@is_in_position, 'IN'))

    LET children = (FOR v IN 1..99 INBOUND start is_in_position
          RETURN v
    )

    RETURN COUNT(children)
  """

  GET_RECENT_POSITIONS = """
    FOR m IN movement
    FILTER @movement_type ? m.type == @movement_type : true
    SORT m.created DESC
    COLLECT position = DOCUMENT(m[@position_type == 'from' ? '_from' : '_to'])
    LIMIT @limit
    RETURN position
  """

  GET_RECENT_MOVEMENT_PRODUCTS = """
    FOR m IN movement
    FILTER m.product_key != null
    FILTER @type ? m.type == @type : true
    SORT m.created DESC
    COLLECT product = DOCUMENT(Product, m.product_key)
    LIMIT @limit
    RETURN product
  """

  SEARCH_MOVEMENTS = """
    FOR m IN movement

    // PRODUCT FILTERS
    let product = FIRST(
        FOR product IN Product
        FILTER product._key == m.product_key
        RETURN product
    )

    FILTER @product_key ? m.product_key == @product_key : true
    LET product_search_context = CONCAT(product.code, ' ', product.description)
    FILTER @product_search ? CONTAINS(LOWER(product_search_context), LOWER(@product_search)) : true

    // SERIAL FILTERS
    FILTER @serial_keys ? m.serial_key IN @serial_keys : true
    LET serial_code = FIRST(FOR s IN Serial FILTER s._key == m.serial_key RETURN s.code)
    FILTER @serial_search ? CONTAINS(LOWER(serial_code), LOWER(@serial_search)) : true

    // POSITION FILTERS

    LET position_from_requested = @position_from ? CONCAT('Position/', @position_from) : 'Position/IN'
    LET position_to_requested = @position_to ? CONCAT('Position/', @position_to) : 'Position/IN'

    LET allowed_positions_from = @position_from && @search_graph ? UNION(
        [position_from_requested],
        (FOR v IN 1..99 INBOUND position_from_requested is_in_position
         FILTER IS_SAME_COLLECTION(v, Position)
         RETURN v._id)
    ) : (@position_from ? [position_from_requested] : [])

    LET allowed_positions_to = @position_to && @search_graph ? UNION(
        [position_to_requested],
        (FOR v IN 1..99 INBOUND position_to_requested is_in_position
         FILTER IS_SAME_COLLECTION(v, Position)
         RETURN v._id)
    ) : (@position_to ? [position_to_requested] : [])

    LET match_from = (@position_from ? m._from IN allowed_positions_from : true)
    LET match_to = (@position_to ? m._to IN allowed_positions_to : true)
    LET position_match = (@position_filter_operator || 'AND') == 'AND'
        ? match_from && match_to
        : match_from || match_to

    FILTER position_match

    // MOVEMENT FILTERS

    FILTER
      (@movement_type ? m.type == @movement_type : true)
      && (@movement_status ? m.status == @movement_status : true)
      && (@include_planned == false ? m.status != 'planned' : true)
      && (@include_completed == false ? m.status != 'completed' : true)
      && (@start_from ? m.start >= @start_from : true)
      && (@start_to ? m.start <= @start_to : true)
      && (@end_from ? m.end >= @end_from : true)
      && (@end_to ? m.end <= @end_to : true)


    // LIST FILTERS
    LET list = FIRST(FOR ml IN MovementList Filter ml._key == m.movement_list_key RETURN ml)
    FILTER
      @list_key ? m.movement_list_key IN @list_key : true
      && (@list_search ? CONTAINS(LOWER(list.code), LOWER(@list_search)) : true)


    // WORK ORDER FILTERS
    LET wo = FIRST(FOR wo IN WorkOrder Filter wo._key == m.references.work_order_key RETURN wo)
    FILTER @work_order_search ? CONTAINS(LOWER(wo.wo_code), LOWER(@work_order_search)) : true


    SORT m.created DESC

    LIMIT @offset, @limit || null

    RETURN MERGE(m, {
      movement_list_code: m.movement_list_key ? FIRST(FOR ml IN MovementList FILTER ml._key == m.movement_list_key RETURN ml.code) : null,
      position_from_key: PARSE_IDENTIFIER(m._from).key,
      position_from_code: DOCUMENT(Position, m._from).code,
      position_to_key: PARSE_IDENTIFIER(m._to).key,
      position_to_code: DOCUMENT(Position, m._to).code,
      serial_code: m.serial_key ? FIRST(FOR s IN Serial FILTER s._key == m.serial_key RETURN s.code) : null,
      product_code: product.code,
      product_description: product.description
    })
  """


  SEARCH_INVENTORY_BY_PRODUCT = """
    // TODO: Add filter by product tag

    FOR p IN Product
    FILTER
      (@product_key ? p._key == @product_key : true)
      && (@product_code ? p.code == @product_code : true)
      && !p.trash
    FOR position, inventory IN 1..99 OUTBOUND p is_in_position
    FILTER inventory.quantity > 0
    RETURN MERGE(
      KEEP(p, '_key', 'code'), {
      position: position.code,
      quantity: inventory.quantity
    })
  """



  SEARCH_MOVEMENT_LISTS = """
    FOR m IN MovementList
    FILTER
      (@search ? CONTAINS(LOWER(m.code), LOWER(@search)) : true)
      && (@list_key ? m.movement_list_key IN @list_key : true)
      && (@includes_product_key ? @includes_product_key IN m.movements[*].product_key : true)
      && (@includes_product_code ? @includes_product_code IN m.movements[* RETURN DOCUMENT(Product, CURRENT.product_key).code] : true)
      && (@due_by_min ? m.due_by >= @due_by_min : true)
      && (@due_by_max ? m.due_by <= @due_by_max : true)
      && (@open_only ? m.status IN ['planned', 'started'] : true)
      && (@status ? m.status IN @status : true)
      && (@type ? m.type == @type : true)
    LIMIT @offset, @limit || null
    RETURN m
  """

  UPDATE_MOVEMENT_LIST = """
    LET list_movements = (
      FOR m IN movement
      FILTER m.movement_list_key == @list_key
      RETURN m
    )
    LET start = MIN(list_movements[*].start)
    LET completed = list_movements[? ALL FILTER CURRENT.status IN ['canceled', 'completed']]
    LET end = completed ? MAX(list_movements[*].end) : null
    LET status = start == null ? 'planned' : (completed ? 'completed' : 'started' )
    UPDATE @list_key WITH { status, start, end } in MovementList
  """



