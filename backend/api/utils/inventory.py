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

  INVENTORY_FILTER = """

    // POSITION
      let position = FIRST(
          FOR position IN Position
          FILTER position._id == e._to
          RETURN position
      )

    FILTER
      IS_SAME_COLLECTION('Product', v)
      && (@position_key ? position._key == @position_key : true)
      && (@position_code ? position.code == @position_code : true)
      && (@product_key ? v._key == @product_key : true)
      && (@product_code ? v.code == @product_code : true)
      && (@owned ? e.owned == @owned : true)
      && (@serial_keys ? e.serial_key IN @serial_keys : true)
      //&& (@contains_position ? @contains_position IN p.vertices[*]._key : true)
      //&& (@search ? LOWER(v.code) LIKE CONCAT('%', LOWER(@search), '%') : true)
      //&& (@has_product_key ? @has_product_key == p.vertices[-1]._key : true)
      //&& (@has_product_code ? @has_product_code == p.vertices[-1].code : true)

    LIMIT @offset, @limit || null

  """

  SEARCH_INVENTORY = """
    FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """


      RETURN merge(v, {
              product_id: v._id,
              product_code: v.code,
              position_id: e._to,
              position_code: position.code,
              serial_key: e.serial_key,
              serial_code: e.serial_key ? FIRST(FOR s IN Serial FILTER s._key == e.serial_key RETURN s.code) : null,
              quantity: e.quantity,
              owned: e.owned,
              value: e.value,
              reference: e.reference,
              date_received: e.date_received,
              expiration_date: e.expiration_date
      })
  """

  SEARCH_INVENTORY_PRODUCT = """
     FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """

      RETURN v
  """

  SEARCH_INVENTORY_POSITIONS = """
     FOR v, e, p IN 1..99 INBOUND 'Position/IN' is_in_position OPTIONS { uniqueVertices: "path" }

    """ + INVENTORY_FILTER + """

      RETURN DISTINCT position
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

  GET_LATEST_RECEIPT_POSITIONS = """
    LET latest_movement_to = (FOR m IN movement
        SORT m.created DESC
        FILTER m.type == 'receipt'
        LIMIT (@limit*10)
        RETURN DISTINCT m._to
    )

    FOR m IN latest_movement_to

    // POSITION_TO
    let position = FIRST(
        FOR position IN Position
        FILTER position._id == m
        RETURN position
    )

    LIMIT @limit

    RETURN position
  """

  GET_LATEST_RECEIPT_PRODUCTS = """
    LET latest_movement_prod = (FOR m IN movement
        SORT m.created DESC
        FILTER m.type == 'receipt'
        LIMIT (@limit*10)
        RETURN DISTINCT m.product_key
    )

    FOR m IN latest_movement_prod

    // PRODUCT
    let product = FIRST(
        FOR product IN Product
        FILTER product._key == m
        RETURN product
    )

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
      && (@mission_key ? m.mission_key == @mission_key : true)
      && (@mission_code ? m.mission_code == @mission_code : true)
      && (@movement_doc ? m.movement_doc == @movement_doc : true)
      && (@source_doc ? m.source_doc == @source_doc : true)
      && (@position_from ? position_from._key == @position_from : true)
      && (@position_to ? position_to._key == @position_to : true)



    LIMIT @offset, @limit || null

    RETURN MERGE(m, {
      product_code: product.code,
      position_from_code: position_from.code,
      position_to_code: position_to.code
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



