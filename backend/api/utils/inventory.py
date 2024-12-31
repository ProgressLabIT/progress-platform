from models.inventory import InventoryMovementReferences

class Queries:

  SEARCH_POSITIONS = """
    LET start = CONCAT('Position/', NOT_NULL(@is_in_position, 'IN'))

    FOR v, e, p IN 1..99 INBOUND start is_in_position

    FILTER
      IS_SAME_COLLECTION('Position', v)
      && (@contains_position ? @contains_position IN p.vertices[*]._key : true)
      && (@search ? LOWER(v.code) LIKE CONCAT('%', LOWER(@search), '%') : true)
      && (@has_product_key ? @has_product_key == p.vertices[-1]._key : true)
      && (@has_product_code ? @has_product_code == p.vertices[-1].code : true)

    LIMIT @offset, @limit || null

    RETURN v
  """

  GET_POSITION_CONTENTS = """
    FOR v, e IN 1..1 INBOUND CONCAT('Position/', @position_key) is_in_position OPTIONS { uniqueVertices: "path" }
    LET position = (IS_SAME_COLLECTION(Position, v) && v.fixed == false) ? MERGE({ type: 'position' }, KEEP(v, '_id', '_key', 'code')) : null
    LET product = IS_SAME_COLLECTION(Product, v) ? MERGE({ type: 'product', quantity: e.quantity }, KEEP(v, '_id', '_key', 'code')) : null
    LET serial = e.serial_key ? FIRST(
      FOR s IN Serial
      FILTER s._key == e.serial_key
      RETURN {
        type: 'serial',
        _id: s._id,
        _key: s._key,
        code: s.code,
        product_key: v._key,
        product_code: v.code,
        quantity: e.quantity
      }
    ): null
    LET result = NOT_NULL(serial, product, position)
    FILTER result != null && result.code != null
    FILTER @search ? (CONTAINS(LOWER(result.code), LOWER(@search)) || CONTAINS(LOWER(result.product_code), LOWER(@search))) : true
    SORT result.code ASC
    LIMIT @limit
    RETURN result
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
        FOR v, e IN 0..9999 ANY start is_in_position OPTIONS { uniqueVertices: "path" }

        RETURN merge({
            position_id: v._id,
            position_key: v._key,
            code: v.code,
            product_key: v.product_key,
            from: e._from,
            to: e._to
        })
  """

  GET_POSITION_CHILDREN_COUNT = """
    LET start = CONCAT('Position/', NOT_NULL(@is_in_position, 'IN'))

    LET children = (FOR v IN 1..99 INBOUND start is_in_position
          RETURN v
    )

    RETURN COUNT(children)
  """

  GET_RECENT_MOVEMENT_START_POSITIONS = """
    FOR m IN movement
    FILTER @type ? m.type == @type : true
    SORT m.created DESC
    COLLECT position_from = DOCUMENT(m._from)
    LIMIT @limit
    RETURN position_from
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

    // PRODUCT
    let product = FIRST(
        FOR product IN Product
        FILTER product._key == m.product_key
        RETURN product
    )

    // POSITION_FROM
    let position_from = FIRST(
        FOR position IN Position
        FILTER position._id == m._from
        RETURN position
    )

    // POSITION_TO
    let position_to = FIRST(
        FOR position IN Position
        FILTER position._id == m._to
        RETURN position
    )

    FILTER
      (@movement_type ? m.type == @movement_type : true)
      && (@movement_status ? m.status == @movement_status : true)
      && (@include_planned == false ? m.status != 'planned' : true)
      && (@start_from ? m.start >= @start_from : true)
      && (@start_to ? m.start <= @start_to : true)
      && (@end_from ? m.end >= @end_from : true)
      && (@end_to ? m.end <= @end_to : true)
      && (@product_key ? m.product_key == @product_key : true)
      && (@product_code ? LENGTH(FOR p IN Product FILTER m.product_key == p._key && CONTAINS(p.code, @product_code) RETURN 1) : true)
      && (@serial_keys ? m.serial_key IN @serial_keys : true)
      && (@list_key ? m.movement_list_key IN @list_key : true)
      && (@position_filter_operator == 'AND' ?
              (@position_from ? position_from._key == @position_from : true) && (@position_to ? position_to._key == @position_to : true) :
              (@position_from ? position_from._key == @position_from : true) || (@position_to ? position_to._key == @position_to : true)
          )


    SORT m.created DESC
    LIMIT @offset, @limit || null

    RETURN MERGE(m, {
      position_from_key: PARSE_IDENTIFIER(m._from).key,
      position_from_code: position_from.code,
      position_to_key: PARSE_IDENTIFIER(m._to).key,
      position_to_code: position_to.code,
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
      && (@type ? m.type IN @type : true)
    LIMIT @offset, @limit || null
    RETURN m
  """


def merge_references(
  list_references: InventoryMovementReferences,
  movement_references: InventoryMovementReferences
  ) -> InventoryMovementReferences:
  """
  Add references from list if not present in the movement.
  This implies an important assumption: movement references do NOT conflict with the list references.
  TODO: enforce consistency either at the model level or in this function.
  """

  merged = dict()
  for attr in InventoryMovementReferences.__fields__.keys():
    list_attr = getattr(list_references, attr)
    movement_attr = getattr(movement_references, attr)
    merged[attr] = movement_attr if movement_attr is not None else list_attr

  return InventoryMovementReferences(**merged)



