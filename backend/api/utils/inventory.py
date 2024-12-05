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

  GET_POSITION_CHILDREN_COUNT = """
    LET start = CONCAT('Position/', NOT_NULL(@is_in_position, 'IN'))

    LET children = (FOR v IN 1..99 INBOUND start is_in_position
          RETURN v
    )

    RETURN COUNT(children)
  """

  SEARCH_MOVEMENTS = """
    FOR m IN movement

    FILTER
      (@movement_type ? m.type == @movement_type : true)
      && (@movement_status ? m.status == @movement_status : true)
      && (@include_planned == false ? m.status != 'planned' : true)
      && (@start_from ? m.start >= @start_from : true)
      && (@start_to ? m.start <= @start_to : true)
      && (@end_from ? m.end >= @end_from : true)
      && (@end_to ? m.end <= @end_to : true)
      && (@product_key ? m.product_key == @product_key : true)
      && (@product_code ? LENGTH(FOR p IN Product FILTER m.product_key == p._key && p.code == @product_code RETURN 1) : true)
      && (@serial_key ? m.serial_key == @serial_key : true)
      && (@serial_code ? m.serial_code == @serial_code : true)
      && (@mission_key ? m.mission_key == @mission_key : true)
      && (@mission_code ? m.mission_code == @mission_code : true)
      && (@movement_doc ? m.movement_doc == @movement_doc : true)
      && (@source_doc ? m.source_doc == @source_doc : true)

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


  SEARCH_INVENTORY_BY_POSITION = """
    // TODO: Add filter by product tag

    LET start = CONCAT('Position/', NOT_NULL(@position_key, 'IN'))


    FOR v,e IN 1..99 INBOUND start is_in_position
    FILTER e.quantity > 0
    COLLECT product_key = v._key AGGREGATE product_stock = SUM(e.quantity)
    RETURN {
      product_key,
      product_code: product.code,
      product_stock
    }
  """
