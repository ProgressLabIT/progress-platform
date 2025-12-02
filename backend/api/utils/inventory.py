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
      && (@search ? REGEX_TEST(v.code, @search, true) : true)
      && (@has_product_key ? @has_product_key == p.vertices[-1]._key : true)
      && (@has_product_code ? @has_product_code == p.vertices[-1].code : true)
      && (@fixed_only ? v.fixed == true : true)

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
    LIMIT @limit + 1
    RETURN {
      _key: e._key,
      type: result.type,
      code: result.code,
      position_key: result.type == 'position' ? v._key : null,
      position_fixed: result.type == 'position' ? v.fixed : null,
      product_code: result.type == 'position' ? null : v.code,
      product_description: result.type == 'position' ? null : v.description,
      product_key: result.type == 'position' ? null : v._key,
      quantity: e.quantity,
      serial_code: result.type == 'serial' ? serial.code : null,
      serial_key: result.type == 'serial' ? serial._key : null
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
      && (@position_search ? REGEX_TEST(position.code, @position_search, true) : true)
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
    FILTER @product_search ? REGEX_TEST(product.code, @product_search, true) : true

    LET start = @root_position_key ? DOCUMENT(Position, @root_position_key) : DOCUMENT('Position/IN')
    FOR path IN 1..99 INBOUND K_PATHS start TO product._id is_in_position
      LET inventory = LAST(path.edges)
      FILTER @owned ? inventory.owned : true
      FILTER @serials_only ? inventory.serial_key != null : true
      FILTER @serial_keys ? inventory.serial_key IN @serial_keys : true
      LET serial_code = DOCUMENT(Serial, inventory.serial_key).code
      FILTER @serial_search ? REGEX_TEST(serial_code, @serial_search, true) : true

      LET p = (
        FOR vertex IN SHIFT(POP(path.vertices)) // Exclude root position IN and final product vertex
        RETURN {
          position_key: vertex._key,
          position_code: vertex.code
        }
      )

      LET shown_path = LENGTH(p) == 0 ? [{ position_key: start._key, position_code: start.code }] : p
      FILTER @position_search
        ? shown_path[? ANY FILTER REGEX_TEST(CURRENT.position_code, @position_search, true)]
        : true

      LIMIT @offset || 0, @limit || null

      RETURN {
        // Show root position in case the product is there (no path)
        path: shown_path,
        quantity: inventory.quantity,
        serial_key: inventory.serial_key,
        product_key: product._key,
        product_code: product.code,
        product_description: product.description,
        serial_code,
        value: inventory.value,
        _key: inventory._key
    }
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
    FILTER @user_key ? m.user_key == @user_key : true
    COLLECT position = DOCUMENT(m[@position_type == 'from' ? '_from' : '_to'])
    AGGREGATE end = MAX(m.end)
    FILTER position != null
    SORT end DESC
    LIMIT @limit
    RETURN position
  """

  GET_RECENT_MOVEMENT_PRODUCTS = """
    FOR m IN movement
    FILTER m.product_key != null
    FILTER @type ? m.type == @type : true
    FILTER @user_key ? m.user_key == @user_key : true
    COLLECT product = DOCUMENT(Product, m.product_key)
    AGGREGATE end = MAX(m.end)
    FILTER product != null && product.active == true && !product.trash
    SORT end DESC
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
    FILTER @product_search ? REGEX_TEST(product.code, @product_search, true) : true

    // SERIAL FILTERS
    FILTER @serial_keys ? m.serial_key IN @serial_keys : true
    LET serial_code = NOT_NULL(m.serial_code, FIRST(FOR s IN Serial FILTER s._key == m.serial_key RETURN s.code))
    FILTER @serial_search ? REGEX_TEST(serial_code, @serial_search, true) : true

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


    SORT m.end DESC, m.start DESC

    LIMIT @offset, @limit || null

    RETURN MERGE(m, {
      movement_list_code: m.movement_list_key ? FIRST(FOR ml IN MovementList FILTER ml._key == m.movement_list_key RETURN ml.code) : null,
      position_from_key: PARSE_IDENTIFIER(m._from).key,
      position_from_code: DOCUMENT(Position, m._from).code,
      position_to_key: PARSE_IDENTIFIER(m._to).key,
      position_to_code: DOCUMENT(Position, m._to).code,
      serial_code,
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
    FOR ml IN MovementList
    FILTER
      (@search ? CONTAINS(LOWER(ml.code), LOWER(@search)) : true)
      && (@list_key ? ml.movement_list_key IN @list_key : true)
      && (@due_by_min ? ml.due_by >= @due_by_min : true)
      && (@due_by_max ? ml.due_by <= @due_by_max : true)
      && (@open_only ? ml.status IN ['planned', 'started'] : true)
      && (@status ? ml.status IN @status : true)
      && (@type ? ml.type == @type : true)
    LIMIT @offset, @limit || null

    LET movements = (FOR m IN movement FILTER m.movement_list_key == ml._key RETURN m)

    FILTER
      (@includes_product_key ? @includes_product_key IN movements[*].product_key : true)
      && (@includes_product_code ? @includes_product_code IN movements[* RETURN DOCUMENT(Product, CURRENT.product_key).code] : true)

    LET planned = COUNT(movements[* FILTER CURRENT.status == 'planned'])
    LET completed = COUNT(movements[* FILTER CURRENT.status == 'completed'])
    RETURN MERGE(ml, { counts: { planned, completed } })
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


  SEARCH_INVENTORY_COUNT_SESSIONS = """
    FOR cs IN InventoryCountSession
    FILTER
      (@search ? REGEX_TEST(cs.code, @search, true) : true)
      && (@status ? cs.status == @status : true)
      && (@type ? cs.type == @type : true)
    LIMIT @offset, @limit || null
    RETURN cs
  """

  SEARCH_INVENTORY_COUNT_ASSIGNMENTS = """
    FOR ica IN InventoryCountAssignment

    FILTER
      (@inventory_count_session_key ? ica.inventory_count_session_key == @inventory_count_session_key : true)
      && (@assignment_type ? ica.assignment_type == @assignment_type : true)
      && (@assigned_to ? ica.assigned_to == @assigned_to : true)
      && (@status ? ica.status == @status : true)

    // Product filters
    FILTER @product_key ? ica.product_key == @product_key : true
    LET product = FIRST(FOR p IN Product FILTER p._key == ica.product_key RETURN p)
    FILTER @product_search ? REGEX_TEST(product.code, @product_search, true) : true

    // Position filters (with hierarchy consideration)
    LET assigned_position = FIRST(FOR p IN Position FILTER p._key == ica.position_key RETURN p)
    FILTER !(@position_key || @position_search) ? true : (
      LET position_key_match = @position_key ? assigned_position._key == @position_key : true
      LET position_code_match = @position_search ? REGEX_TEST(assigned_position.code, @position_search, true) : true

      LET children = (
        FOR p IN 1..9999 INBOUND CONCAT('Position/', ica.position_key) is_in_position
        FILTER IS_SAME_COLLECTION(Position, p)
        RETURN p
      )

      LET children_key_match = @position_key ? @position_key IN children[*]._key : true
      LET children_code_match = @position_search ? children[*].code[? ANY FILTER REGEX_TEST(CURRENT, @position_search, true)] : true

      RETURN position_key_match && position_code_match && children_key_match && children_code_match
    )

    SORT ica[@order_by]

    LIMIT @offset, @limit || null

    RETURN MERGE(ica, {
      product_code: product.code,
      product_description: product.description,
      position_code: assigned_position ? assigned_position.code : null
    })
  """

  GET_COUNT_SESSION_DETAILS = """
    FOR cs IN InventoryCountSession
    FILTER cs._key == @inventory_count_session_key
    LET target_collection_name = { 'product': 'Product', 'position': 'Position' }[cs.type]
    LET assignments = MERGE(
      FOR ica IN InventoryCountAssignment
      FILTER ica.inventory_count_session_key == @inventory_count_session_key && ica.status != 'canceled'
      LET target_data = KEEP(DOCUMENT(target_collection_name, ica.target_key), 'code', 'description')
      FILTER target_data != null
      LET assignment = { _key: ica._key, target_key: ica.target_key, status: ica.status, target_data, include_children: ica.include_children }
      COLLECT assignee = ica.assigned_to INTO assignment_group KEEP assignment
      RETURN { [assignee]: assignment_group[*].assignment }
    )
    RETURN MERGE(cs, { assignments })
  """

  CANCEL_INVENTORY_COUNT_ASSIGNMENTS = """
    FOR ica IN InventoryCountAssignment
    FILTER ica._key IN @assignment_keys && ica.status == 'planned'
    UPDATE ica WITH { status: 'canceled' } in InventoryCountAssignment
    RETURN OLD._key
  """

  SEARCH_INVENTORY_COUNT_RECORDS = """
    FOR r IN inventory_count_record
    FILTER
      (@count_session_key ? r.inventory_count_session_key == @count_session_key : true)
      && (@assignment_key ? r.assignment_key == @assignment_key : true)
      && (@product_key ? r._from == @product_key : true)
      && (@position_key ? r._to == @position_key : true)
      && (@user_key ? r.user_key == @user_key : true)
      && (@include_started ? r.status == 'started' : true)
      && (@include_completed ? r.status == 'completed' : true)
      && (@include_discarded ? r.status == 'discarded' : true)
    LET product = FIRST(FOR p IN Product FILTER p._key == PARSE_IDENTIFIER(r._from).key RETURN p)
    LET position = FIRST(FOR p IN Position FILTER p._key == PARSE_IDENTIFIER(r._to).key RETURN p)
    LIMIT @offset,@limit || null
    RETURN MERGE(r, {
      product_key: product._key,
      product_code: product.code,
      product_description: product.description,
      product_traceability_level: product.traceability_level,
      product_tags: product.tags,
      position_key: position._key,
      position_code: position.code
    })
  """
